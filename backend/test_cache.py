import asyncio
from app.core.job_cache import get_cached_analyses, save_to_cache

fake_listings = [
    {"id": "test123", "source": "adzuna", "title": "Test AI Engineer", "description": "Requires Python and LangGraph."},
]

async def main():
    print("=== First check (should be empty) ===")
    cache_map = await get_cached_analyses(fake_listings)
    print(f"Cache hits: {len(cache_map)}")

    print("\n=== Saving a fake analysis result ===")
    fake_analyzed = [{
        "id": "test123", "source": "adzuna",
        "required_skills": ["Python", "LangGraph"], "preferred_skills": [],
        "seniority_level": "mid", "min_experience_years": 2,
        "employment_type": "full-time", "key_responsibilities": ["Build agents"],
        "description_length": 40,
    }]
    await save_to_cache(fake_analyzed)

    print("\n=== Second check (should now hit cache) ===")
    cache_map = await get_cached_analyses(fake_listings)
    print(f"Cache hits: {len(cache_map)}")
    print(f"Cached data: {cache_map}")

if __name__ == "__main__":
    asyncio.run(main())