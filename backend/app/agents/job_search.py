from app.agents.state import GraphState
from app.mcp_servers.job_board_client import search_all_sources


async def job_search_node(state: GraphState) -> GraphState:
    preferences = state.get("preferences", {})
    role = preferences.get("role", "")
    locations = preferences.get("locations", [])

    print(f"[JobSearch] querying via MCP: role='{role}', locations={locations}")

    all_listings = []
    for loc in locations or [""]:  # fall back to one unscoped search if no locations given
        listings = await search_all_sources(role=role, location=loc, results_limit=7)
        all_listings.extend(listings)

    # dedupe across locations too (a job could surface under two location queries)
    from app.mcp_servers.job_board_client import _dedupe_listings
    state["raw_listings"] = _dedupe_listings(all_listings)
    return state