import asyncio
import sys
import os
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langgraph.types import Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents.graph import build_graph

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL").replace("+asyncpg", "")


async def main():
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)

        config = {"configurable": {"thread_id": "test-thread-refine"}}

        initial_state = {
            "candidate_profile": {"name": "Akash"},
            "preferences": {"role": "Backend Engineer", "location": "Remote"},
            "raw_listings": [],
            "analyzed_jobs": [],
            "ranked_jobs": [],
            "explanations": {},
            "iteration": 0,
            "user_feedback": None,
        }

        print("=== Run 1: initial search ===")
        r1 = await graph.ainvoke(initial_state, config=config)
        print("Ranked jobs:", r1.get("ranked_jobs"))

        print("\n=== Run 2: refine salary only (should skip job_search, hit matching_ranking) ===")
        r2 = await graph.ainvoke(
            Command(resume={"approved": False, "updated_preferences": {"salary_min": 80000}}),
            config=config,
        )
        print("Preferences now:", r2.get("preferences"), "| iteration:", r2.get("iteration"))

        print("\n=== Run 3: refine location (should trigger supervisor -> job_search again) ===")
        r3 = await graph.ainvoke(
            Command(resume={"approved": False, "updated_preferences": {"location": "Bangalore"}}),
            config=config,
        )
        print("Preferences now:", r3.get("preferences"), "| iteration:", r3.get("iteration"))

        print("\n=== Run 4: approve ===")
        r4 = await graph.ainvoke(
            Command(resume={"approved": True}),
            config=config,
        )
        print("Final:", r4)


if __name__ == "__main__":
    asyncio.run(main())