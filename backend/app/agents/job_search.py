from app.agents.state import GraphState
from app.mcp_servers.job_board_client import search_all_sources

async def job_search_node(state: GraphState) -> GraphState:
    """
    Fetches live job listings via the Job Board MCP server, using
    the current preferences in state.
    """
    preferences = state.get("preferences", {})
    role = preferences.get("role", "")
    location = preferences.get("location", "")

    print(f"[JobSearch] querying Adzuna via MCP: role='{role}', location='{location}'")

    listings = await search_all_sources(role=role, location=location, results_limit=10)

    state["raw_listings"] = listings
    return state