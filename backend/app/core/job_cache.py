import json
import os
from typing import Dict, Tuple, List
from upstash_redis import Redis

CACHE_TTL_HOURS = 24  # job postings/requirements can change; don't cache indefinitely

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Initialize Upstash Redis client
try:
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if url and token:
        redis_client = Redis(url=url, token=token)
    else:
        redis_client = None
except Exception as e:
    redis_client = None


def _get_cache_key(job_id: str, source: str) -> str:
    """Generate a consistent cache key for a job listing."""
    return f"job_analysis:{source}:{job_id}"


async def get_cached_analyses(listings: list[dict]) -> dict[tuple[str, str], dict]:
    """
    Looks up cached analysis results for the given listings.
    Returns a dict keyed by (job_id, source) for entries still within TTL.
    """
    if not listings or not redis_client:
        return {}

    # Extract keys we want to fetch
    cache_keys = []
    mapping = {}
    
    for job in listings:
        job_id = str(job.get("id", ""))
        source = str(job.get("source", ""))
        if job_id and source:
            key = _get_cache_key(job_id, source)
            cache_keys.append(key)
            mapping[key] = (job_id, source)
            
    if not cache_keys:
        return {}

    try:
        # MGET retrieves multiple keys at once
        results = redis_client.mget(*cache_keys)
    except Exception as e:
        print(f"Redis mget error: {e}")
        return {}

    cache_map = {}
    for key, result_str in zip(cache_keys, results):
        if result_str:
            try:
                # Upstash Python client handles JSON parsing if it was saved as JSON string
                analysis_data = json.loads(result_str) if isinstance(result_str, str) else result_str
                
                # Recover the original tuple key
                tuple_key = mapping[key]
                cache_map[tuple_key] = analysis_data
            except Exception as e:
                print(f"Error parsing redis cache item for {key}: {e}")

    return cache_map


async def save_to_cache(analyzed_jobs: list[dict]) -> None:
    """Upserts freshly analyzed jobs into the cache."""
    if not analyzed_jobs or not redis_client:
        return

    # Calculate TTL in seconds
    ttl_seconds = CACHE_TTL_HOURS * 3600
    
    # We could use pipeline for batch insertion, but standard client loop is fine for now
    for job in analyzed_jobs:
        job_id = str(job.get("id", ""))
        source = str(job.get("source", ""))
        if not job_id or not source:
            continue

        key = _get_cache_key(job_id, source)
        
        analysis_fields = {
            k: v for k, v in job.items()
            if k not in ("id", "source", "title", "company", "location", "redirect_url", "salary_min", "salary_max")
        }

        try:
            # Set the value with an expiration (ex=seconds)
            redis_client.set(key, json.dumps(analysis_fields), ex=ttl_seconds)
        except Exception as e:
            print(f"Redis set error for {key}: {e}")
