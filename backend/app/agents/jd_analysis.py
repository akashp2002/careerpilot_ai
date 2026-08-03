import asyncio
from app.agents.state import GraphState
from app.core.job_analyzer import analyze_job_listing

MAX_CONCURRENT_ANALYSES = 3


async def jd_analysis_node(state: GraphState) -> GraphState:
    """
    Analyzes each raw job listing into structured form. Runs with
    bounded concurrency to speed things up without tripping Groq's
    rate limits.x
    """
    raw_listings = state.get("raw_listings", [])
    print(f"[JDAnalysis] analyzing {len(raw_listings)} listings...")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)

    async def analyze_with_limit(job: dict):
        async with semaphore:
            return await asyncio.to_thread(analyze_job_listing, job)

    results = await asyncio.gather(
        *(analyze_with_limit(job) for job in raw_listings),
        return_exceptions=True,
    )

    analyzed = []
    for job, result in zip(raw_listings, results):
        if isinstance(result, Exception):
            print(f"[JDAnalysis] failed to analyze '{job.get('title')}': {result}")
            continue
        analyzed.append(result.model_dump())

    state["analyzed_jobs"] = analyzed
    return state