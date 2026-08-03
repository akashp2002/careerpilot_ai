import asyncio
from app.agents.state import GraphState
from app.core.explainer import generate_explanation

TOP_N_TO_EXPLAIN = 5
MAX_CONCURRENT_EXPLANATIONS = 2


def build_candidate_summary(candidate_profile: dict) -> str:
    skills = candidate_profile.get("skills", [])
    experience = candidate_profile.get("experience", [])
    projects = candidate_profile.get("projects", [])

    parts = []
    if skills:
        parts.append(f"Skills: {', '.join(skills[:10])}")
    if experience:
        titles = [e.get("title", "") for e in experience]
        parts.append(f"Experience: {', '.join(titles)}")
    else:
        parts.append("No formal work experience (fresher)")
    if projects:
        parts.append(f"Notable projects: {', '.join(p.get('name', '') for p in projects[:3])}")

    return " | ".join(parts)


async def explanation_node(state: GraphState) -> GraphState:
    ranked_jobs = state.get("ranked_jobs", [])
    candidate_profile = state.get("candidate_profile", {})

    top_jobs = ranked_jobs[:TOP_N_TO_EXPLAIN]
    print(f"[Explanation] generating explanations for top {len(top_jobs)} jobs...")

    candidate_summary = build_candidate_summary(candidate_profile)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXPLANATIONS)

    async def explain_with_limit(job: dict):
        async with semaphore:
            return await asyncio.to_thread(generate_explanation, candidate_summary, job)

    results = await asyncio.gather(
        *(explain_with_limit(job) for job in top_jobs),
        return_exceptions=True,
    )

    explanations = {}
    for job, result in zip(top_jobs, results):
        if isinstance(result, Exception):
            print(f"[Explanation] failed for '{job.get('title')}': {result}")
            explanations[job["id"]] = "Explanation unavailable."
        else:
            explanations[job["id"]] = result

    state["explanations"] = explanations
    return state