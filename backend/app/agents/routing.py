from app.agents.state import GraphState

SOURCE_AFFECTING_FIELDS = {"role", "locations"}


def route_after_hitl(state: GraphState) -> str:
    feedback = state.get("user_feedback") or {}

    if feedback.get("approved"):
        return "end"

    updated = feedback.get("updated_preferences", {})
    changed_fields = set(updated.keys())

    if changed_fields & SOURCE_AFFECTING_FIELDS:
        return "supervisor"        # role/location changed -> full re-search
    else:
        return "matching_ranking"  # only salary/remote etc changed -> re-rank existing listings