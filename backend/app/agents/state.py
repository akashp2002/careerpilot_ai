from typing import TypedDict, Optional


class GraphState(TypedDict):
    candidate_profile: dict
    preferences: dict
    raw_listings: list[dict]
    analyzed_jobs: list[dict]
    ranked_jobs: list[dict]
    explanations: dict[str, str]
    iteration: int
    user_feedback: Optional[dict]