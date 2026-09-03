import asyncio
from app.agents.state import GraphState
from app.core.job_analyzer import analyze_job_batch
from app.core.job_cache import get_cached_analyses, save_to_cache

MAX_LISTINGS_TO_ANALYZE = 15
BATCH_SIZE = 5
MAX_CONCURRENT_BATCHES = 3


async def jd_analysis_node(state: GraphState) -> GraphState:
    raw_listings = state.get("raw_listings", [])[:MAX_LISTINGS_TO_ANALYZE]

    cache_map = await get_cached_analyses(raw_listings)
    print(f"[JDAnalysis-DEBUG] cache_map returned {len(cache_map)} entries, keys: {list(cache_map.keys())}")

    cached_results = []
    needs_analysis = []
    for job in raw_listings:
        key = (job.get("id", ""), job.get("source", ""))
        if key in cache_map:
            cached_results.append({**job, **cache_map[key]})
        else:
            needs_analysis.append(job)

    print(f"[JDAnalysis] {len(cached_results)} from cache, analyzing {len(needs_analysis)} fresh (batches of {BATCH_SIZE})...")

    analyzed = list(cached_results)

    if needs_analysis:
        batches = [needs_analysis[i:i + BATCH_SIZE] for i in range(0, len(needs_analysis), BATCH_SIZE)]
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)

        async def analyze_batch_with_limit(batch: list[dict]):
            async with semaphore:
                return await asyncio.to_thread(analyze_job_batch, batch)

        batch_results = await asyncio.gather(
            *(analyze_batch_with_limit(batch) for batch in batches),
            return_exceptions=True,
        )

        fresh_analyzed = []
        for batch, result in zip(batches, batch_results):
            if isinstance(result, Exception):
                titles = [j.get("title") for j in batch]
                print(f"[JDAnalysis] batch failed for {titles}: {result}")
                continue
            fresh_analyzed.extend([r.model_dump() for r in result])

        await save_to_cache(fresh_analyzed)
        analyzed.extend(fresh_analyzed)

    state["analyzed_jobs"] = analyzed
    return state