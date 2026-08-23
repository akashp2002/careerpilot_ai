from app.agents.state import GraphState

SOURCE_AFFECTING_FIELDS = {"role", "locations"}

def route_after_hitl(state: GraphState) -> str:
    feedback = state.get("user_feedback") or {}

    if feedback.get("approved"):
        return "end"

    updated = feedback.get("updated_preferences", {})
    
    # Check which source-affecting fields were actually provided and are not empty
    changed_source_fields = {
        field for field in SOURCE_AFFECTING_FIELDS 
        if updated.get(field) not in (None, "", [])
    }

    # If role or locations were actually changed/provided, do a full re-search
    if changed_source_fields:
        return "supervisor"
    
    # Otherwise, only salary/remote/etc. changed -> re-rank existing listings
    return "matching_ranking"