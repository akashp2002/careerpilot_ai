import asyncio
from app.mcp_servers.job_board_client import  search_all_sources

async def main():
    for term in ["AI Engineer", "Applied AI Engineer", "Machine Learning Engineer"]:
        results = await  search_all_sources(term, "Bangalore", results_limit=5)
        print(f"'{term}' -> {len(results)} listings")
        for job in results[:3]:
            print(f"   - {job['title']} @ {job['company']}")

if __name__ == "__main__":
    asyncio.run(main())