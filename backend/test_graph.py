from app.agents.graph import graph

initial_state = {
    "candidate_profile": {"name": "Akash"},
    "preferences": {"role": "Backend Engineer", "location": "Remote"},
    "raw_listings": [],
    "analyzed_jobs": [],
    "ranked_jobs": [],
    "explanations": {},
    "iteration": 0,
    "user_feedback": None,
}

result = graph.invoke(initial_state)
print("\nFinal state:")
print(result)