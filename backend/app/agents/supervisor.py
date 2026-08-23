import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.agents.state import GraphState
from app.core.groq_utils import call_with_retry

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


def expand_search_terms(role: str, candidate_skills: list[str]) -> list[str]:
    """Uses LLM reasoning to suggest alternate job title phrasings for broader search coverage."""
    context = f"Requested role: {role}\nCandidate skills: {', '.join(candidate_skills[:15])}"

    try:
        response = call_with_retry(lambda: client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.2,
        ))
        content = response.choices[0].message.content.strip()
        alternates = json.loads(content)
        return [role] + [a for a in alternates if isinstance(a, str) and a.lower() != role.lower()]
    except Exception as e:
        print(f"[Supervisor] search term expansion failed, using original role only: {e}")
        return [role]


def supervisor_node(state: GraphState) -> GraphState:
    preferences = state.get("preferences", {})
    candidate_profile = state.get("candidate_profile", {})
    role = preferences.get("role", "")

    search_terms = expand_search_terms(role, candidate_profile.get("skills", []))

    print(f"[Supervisor] iteration={state.get('iteration', 0)} | role='{role}' -> search_terms={search_terms}")

    state["preferences"] = {**preferences, "_expanded_roles": search_terms}
    return state