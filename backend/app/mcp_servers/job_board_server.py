import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")

mcp = FastMCP("job-board-server")


@mcp.tool()
def search_jobs(role: str, location: str, results_limit: int = 10) -> list[dict]:
    """
    Search live job listings via the Adzuna API.

    Args:
        role: Job title or keywords to search for (e.g. "Backend Engineer")
        location: Location to search in (e.g. "Bangalore", "Remote")
        results_limit: Max number of listings to return (default 10)
    """
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "title_only": role,
        "where": location,
        "results_per_page": results_limit,
        "content-type": "application/json",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    listings = []
    for job in data.get("results", []):
        listings.append({
            "id": str(job.get("id","")),
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "description": job.get("description"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "redirect_url": job.get("redirect_url"),
        })

    return listings

@mcp.tool()
def search_remoteok_jobs(role: str, results_limit: int = 10) -> list[dict]:
    """
    Search remote job listings via RemoteOK's public API. RemoteOK is
    remote-only (no location filtering) but returns full, untruncated
    job descriptions unlike Adzuna's 500-char snippets.

    Args:
        role: Job title or keywords to filter for (matched against title)
        results_limit: Max number of listings to return (default 10)
    """
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "CareerPilotAI/1.0"}

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    # First element is API metadata/legal notice, not a job listing
    jobs = data[1:] if data and "legal" in data[0] else data

    role_lower = role.lower()
    matched = []

    for job in jobs:
        title = job.get("position", "")
        if role_lower in title.lower():
            matched.append({
                "id": str(job.get("id","")),
                "title": title,
                "company": job.get("company"),
                "location": job.get("location") or "Remote",
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min") or None,
                "salary_max": job.get("salary_max") or None,
                "redirect_url": job.get("url") or job.get("apply_url", ""),
            })
        if len(matched) >= results_limit:
            break

    return matched


if __name__ == "__main__":
    mcp.run()