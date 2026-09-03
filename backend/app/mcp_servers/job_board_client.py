from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio


def get_server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command="python",
        args=["-m", "app.mcp_servers.job_board_server"],
    )


@asynccontextmanager
async def job_board_session():
    params = get_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

async def search_adzuna_via_mcp(role: str, location: str, results_limit: int = 10) -> list[dict]:
    async with job_board_session() as session:
        result = await session.call_tool(
            "search_jobs",
            {"role": role, "location": location, "results_limit": results_limit},
        )
        if result.isError:
            raise RuntimeError(f"Adzuna MCP tool error: {result.content}")
        if not result.content:
            return []
        import json
        return json.loads(result.content[0].text)


async def search_remoteok_via_mcp(role: str, results_limit: int = 10) -> list[dict]:
    async with job_board_session() as session:
        result = await session.call_tool(
            "search_remoteok_jobs",
            {"role": role, "results_limit": results_limit},
        )
        if result.isError:
            raise RuntimeError(f"RemoteOK MCP tool error: {result.content}")
        if not result.content:
            return []
        import json
        return json.loads(result.content[0].text)


def _dedupe_listings(listings: list[dict]) -> list[dict]:
    """Dedupes cross-posted jobs by normalized title+company pair, then
    sorts by a stable key so repeated searches with the same underlying
    jobs consistently select the same subset - maximizing JD Analysis
    cache hit rate across runs, since the external APIs don't guarantee
    stable ordering between calls."""
    seen = set()
    deduped = []
    for job in listings:
        key = (job.get("title", "").strip().lower(), job.get("company", "").strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(job)

    deduped.sort(key=lambda j: (j.get("source", ""), j.get("id", "")))
    return deduped

async def search_all_sources(role: str, location: str, results_limit: int = 10) -> list[dict]:
    """
    Fans out to both job sources concurrently, merges and dedupes results.
    Individual source failures don't crash the whole search.
    """
    results = await asyncio.gather(
        search_adzuna_via_mcp(role, location, results_limit),
        search_remoteok_via_mcp(role, results_limit),
        return_exceptions=True,
    )

    combined = []
    for source_name, result in zip(["Adzuna", "RemoteOK"], results):
        if isinstance(result, Exception):
            print(f"[JobBoardClient] {source_name} failed: {result}")
            continue
        combined.extend(result)

    return _dedupe_listings(combined)