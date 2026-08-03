from app.agents.state import GraphState


def supervisor_node(state: GraphState) -> GraphState:
    """
    Entry/routing node. In the full version, this decides which job
    sources to query based on preferences. For the skeleton, it just
    logs and passes state through unchanged.
    """
    print(f"[Supervisor] iteration={state.get('iteration', 0)} | preferences={state.get('preferences')}")
    return state