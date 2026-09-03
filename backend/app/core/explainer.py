import os
from groq import Groq
from dotenv import load_dotenv
from app.core.llm_client import get_structured_completion
from langsmith import traceable


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a career advisor explaining job match results to a candidate.
You will be given the candidate's key background and a job's score breakdown (real
computed data, not your judgment). Write a short, honest, encouraging explanation
(2-4 sentences) of why this job scored the way it did.

RULES:
- Base your explanation ONLY on the data provided. Do not invent skills, requirements,
  or facts not present in the input.
- Reference specific matched/missing skills by name when available.
- If data_completeness is low, mention that the job posting had limited details.
- If a seniority mismatch was flagged, mention it honestly but constructively.
- Keep it concise and conversational, not robotic. No markdown, no bullet points.
"""

@traceable(name="explanation_llm_call")
def generate_explanation(candidate_summary: str, job: dict) -> str:
    breakdown = job.get("score_breakdown", {})

    context = f"""
Candidate background: {candidate_summary}

Job: {job.get('title')} at {job.get('company')}
Overall match score: {job.get('match_score')}%

Score breakdown:
- Semantic fit: {breakdown.get('semantic_similarity')}%
- Skill overlap: {breakdown.get('skill_overlap')}%
- Matched skills: {breakdown.get('matched_skills') or 'none identified'}
- Missing skills: {breakdown.get('missing_skills') or 'none identified'}
- Experience match: {breakdown.get('experience_match')}%
- Location match: {breakdown.get('location_match')}%
- Data completeness: {breakdown.get('data_completeness')}% (how much structured info was available from the posting)
- Seniority mismatch flagged: {breakdown.get('seniority_penalty_applied')}
"""

    return get_structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_content=context,
        groq_model="openai/gpt-oss-20b",
        temperature=0.3,
    )

