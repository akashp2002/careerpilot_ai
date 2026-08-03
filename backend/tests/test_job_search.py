import pytest

from app.agents import job_search


class DummySearchAllSources:
    def __init__(self):
        self.calls = []

    async def __call__(self, role, location, results_limit=10):
        self.calls.append((role, location, results_limit))
        return [{"id": f"{location or 'all'}"}]


@pytest.mark.asyncio
async def test_job_search_uses_preferences_locations(monkeypatch):
    calls = []

    async def fake_search_all_sources(role, location, results_limit=10):
        calls.append((role, location, results_limit))
        return [{"id": location or "all"}]

    monkeypatch.setattr(job_search, "search_all_sources", fake_search_all_sources)

    state = {
        "preferences": {"role": "AI Engineer", "locations": ["mumbai", "bangalore"]},
        "raw_listings": [],
    }

    result = await job_search.job_search_node(state)

    assert calls == [
        ("AI Engineer", "mumbai", 10),
        ("AI Engineer", "bangalore", 10),
    ]
    assert len(result["raw_listings"]) == 2
