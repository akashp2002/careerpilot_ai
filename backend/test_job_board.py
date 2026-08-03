import asyncio
from app.mcp_servers.job_board_client import search_jobs_via_mcp


async def main():
    results = await search_jobs_via_mcp("Backend Engineer", "Bangalore", results_limit=5)
    print(f"Got {len(results)} listings:")
    for job in results:
        print(f" - {job['title']} @ {job['company']} ({job['location']})")


if __name__ == "__main__":
    asyncio.run(main())