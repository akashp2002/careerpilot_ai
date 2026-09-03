import json
from datetime import datetime, timedelta
from sqlalchemy import select
from app.agents.state import GraphState
from app.core.llm_client import get_structured_completion
from app.core.database import AsyncSessionLocal
from app.models.db_models import SearchTermCache

SEARCH_TERM_CACHE_TTL_HOURS = 24

SYSTEM_PROMPT = """You are a job search strategist. Given a candidate's role
request and their background, suggest up to 3 alternate job title phrasings
that represent the SAME role in the job market (not different roles).

Example: "AI Engineer" with an ML/LangGraph background might also be searched
as "Machine Learning Engineer" or "Applied AI Engineer".

RULES:
- Only suggest genuine synonyms/variants of the SAME role, never a different role.
- Base suggestions on the candidate's actual skills/background provided.
- If the role is already unambiguous and standard, return fewer or zero alternates.
- Return ONLY a JSON array of strings, e.g. ["Machine Learning Engineer", "Applied AI Engineer"]
- No markdown, no preamble, no explanation.
"""


async def _get_cached_terms(role: str) -> list[str] | None:
    cutoff = datetime.utcnow() - timedelta(hours=SEARCH_TERM_CACHE_TTL_HOURS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SearchTermCache).where(
                SearchTermCache.role == role.lower(),
                SearchTermCache.cached_at >= cutoff,
            )
        )
        row = result.scalar_one_or_none()
        return row.expanded_terms if row else None


async def _save_terms_to_cache(role: str, terms: list[str]) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.get(SearchTermCache, role.lower())
        if existing:
            existing.expanded_terms = terms
            existing.cached_at = datetime.utcnow()
        else:
            session.add(SearchTermCache(role=role.lower(), expanded_terms=terms))
        await session.commit()


def expand_search_terms(role: str, candidate_skills: list[str]) -> list[str]:
    """Uses LLM reasoning to suggest alternate job title phrasings for broader search coverage."""
    context = f"Requested role: {role}\nCandidate skills: {', '.join(candidate_skills[:15])}"

    try:
        content = get_structured_completion(
            system_prompt=SYSTEM_PROMPT,
            user_content=context,
            groq_model="openai/gpt-oss-20b",
            temperature=0,  # was 0.2 - determinism matters more here than phrasing variety, since this feeds the cache
        )
        alternates = json.loads(content)
        return [role] + [a for a in alternates if isinstance(a, str) and a.lower() != role.lower()]
    except Exception as e:
        print(f"[Supervisor] search term expansion failed, using original role only: {e}")
        return [role]


async def supervisor_node(state: GraphState) -> GraphState:
    preferences = state.get("preferences", {})
    candidate_profile = state.get("candidate_profile", {})
    role = preferences.get("role", "")

    cached_terms = await _get_cached_terms(role)
    if cached_terms:
        print(f"[Supervisor] using cached search terms for role='{role}'")
        search_terms = cached_terms
    else:
        search_terms = expand_search_terms(role, candidate_profile.get("skills", []))
        await _save_terms_to_cache(role, search_terms)

    print(f"[Supervisor] iteration={state.get('iteration', 0)} | role='{role}' -> search_terms={search_terms}")

    state["preferences"] = {**preferences, "_expanded_roles": search_terms}
    return state