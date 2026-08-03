from app.agents.state import GraphState
from app.core.matcher import score_jobs


def matching_ranking_node(state: GraphState) -> GraphState:
    candidate_profile = state.get("candidate_profile", {})
    analyzed_jobs = state.get("analyzed_jobs", [])
    preferences = state.get("preferences", {})

    print(f"[MatchingRanking] scoring {len(analyzed_jobs)} jobs against candidate profile...")

    ranked = score_jobs(candidate_profile, analyzed_jobs, preferences)

    state["ranked_jobs"] = ranked
    return state