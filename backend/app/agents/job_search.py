import asyncio
from app.agents.state import GraphState
from app.mcp_servers.job_board_client import search_adzuna_via_mcp, search_remoteok_via_mcp, _dedupe_listings

MAX_CONCURRENT_SEARCHES = 3


async def job_search_node(state: GraphState) -> GraphState:
    preferences = state.get("preferences", {})
    search_terms = preferences.get("_expanded_roles") or [preferences.get("role", "")]
    locations = preferences.get("locations", []) or [""]

    print(f"[JobSearch] querying via MCP: terms={search_terms}, locations={locations}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)

    async def adzuna_with_limit(term: str, loc: str):
        async with semaphore:
            return await search_adzuna_via_mcp(term, loc, results_limit=10)

    async def remoteok_with_limit(term: str):
        async with semaphore:
            return await search_remoteok_via_mcp(term, results_limit=10)

    # Adzuna genuinely needs one call per (term, location) - it's location-scoped server-side
    adzuna_tasks = [adzuna_with_limit(term, loc) for term in search_terms for loc in locations]

    # RemoteOK ignores location entirely - only fetch once per term, not per (term, location)
    remoteok_tasks = [remoteok_with_limit(term) for term in search_terms]

    adzuna_results, remoteok_results = await asyncio.gather(
        asyncio.gather(*adzuna_tasks, return_exceptions=True),
        asyncio.gather(*remoteok_tasks, return_exceptions=True),
    )

    import traceback

    all_listings = []
    for result in [*adzuna_results, *remoteok_results]:
        if isinstance(result, Exception):
            print(f"[JobSearch] a search call failed:")
            traceback.print_exception(type(result), result, result.__traceback__)
            continue
        all_listings.extend(result)

    state["raw_listings"] = _dedupe_listings(all_listings)
    return state