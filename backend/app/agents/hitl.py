from langgraph.types import interrupt
from app.agents.state import GraphState


def hitl_node(state: GraphState) -> GraphState:
    """
    Pauses for human review. Resume payload shape:
      {"approved": True}
      OR
      {"approved": False, "updated_preferences": {...}}
    """
    feedback = interrupt({
        "message": "Review results",
        "ranked_jobs": state.get("ranked_jobs", []),
    })

    print(f"[HITL-DEBUG] feedback={feedback}")
    print(f"[HITL-DEBUG] preferences before merge={state.get('preferences')}")

    state["user_feedback"] = feedback

    if not feedback.get("approved") and "updated_preferences" in feedback:
        state["preferences"] = {**state["preferences"], **feedback["updated_preferences"]}
        state["iteration"] = state.get("iteration", 0) + 1

    print(f"[HITL-DEBUG] preferences after merge={state.get('preferences')}")

    return state