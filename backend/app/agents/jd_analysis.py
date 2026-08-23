import asyncio
from app.agents.state import GraphState
from app.core.job_analyzer import analyze_job_batch

MAX_LISTINGS_TO_ANALYZE = 15
BATCH_SIZE = 5
MAX_CONCURRENT_BATCHES = 3


async def jd_analysis_node(state: GraphState) -> GraphState:
    raw_listings = state.get("raw_listings", [])[:MAX_LISTINGS_TO_ANALYZE]
    print(f"[JDAnalysis] analyzing {len(raw_listings)} listings in batches of {BATCH_SIZE}...")

    batches = [raw_listings[i:i + BATCH_SIZE] for i in range(0, len(raw_listings), BATCH_SIZE)]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)

    async def analyze_batch_with_limit(batch: list[dict]):
        async with semaphore:
            return await asyncio.to_thread(analyze_job_batch, batch)

    batch_results = await asyncio.gather(
        *(analyze_batch_with_limit(batch) for batch in batches),
        return_exceptions=True,
    )

    analyzed = []
    for batch, result in zip(batches, batch_results):
        if isinstance(result, Exception):
            titles = [j.get("title") for j in batch]
            print(f"[JDAnalysis] batch failed for {titles}: {result}")
            continue
        analyzed.extend([r.model_dump() for r in result])

    state["analyzed_jobs"] = analyzed
    return state