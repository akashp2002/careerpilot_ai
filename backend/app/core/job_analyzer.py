import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from app.models.job import AnalyzedJob
from app.core.groq_utils import call_with_retry
from langsmith import traceable

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a job description analysis engine. Extract structured
information from the provided job listing into strict JSON matching this schema:

{
  "required_skills": [str],
  "preferred_skills": [str],
  "seniority_level": "entry"|"mid"|"senior"|"lead"|null,
  "min_experience_years": int|null,
  "employment_type": str|null,
  "key_responsibilities": [str]
}

RULES FOR required_skills / preferred_skills:
- Only include concrete, nameable skills: programming languages, frameworks,
  libraries, tools, platforms, databases, cloud services, protocols, or
  well-established technical methodologies (e.g. "Python", "React", "Kubernetes",
  "REST APIs", "CI/CD", "machine learning").
- Do NOT include: the job title itself, soft-skill phrases ("high-caliber
  engineering team", "strong communication"), vague nouns without a named
  technology ("platforms", "AI systems", "modern tools"), or full sentences /
  clauses copied from the posting.
- Each entry should be a short skill name (1-4 words), not a paraphrased sentence.
- If a requirement is described only vaguely with no nameable skill (e.g. "familiarity
  with AI frameworks"), skip it rather than inventing a generic entry - do not pad
  the list.

RULES (general):
- Extract ONLY what is explicitly stated or clearly implied by the text.
- Distinguish required vs preferred/nice-to-have skills if the text differentiates them.
- If the description is truncated or vague, extract what you can and leave the rest null/empty.
- Return ONLY the JSON object. No markdown, no backticks, no preamble.
"""

@traceable(name="jd_analysis_llm_call")
def analyze_job_listing(raw_job: dict, max_retries: int = 2) -> AnalyzedJob:
    description = raw_job.get("description", "")

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = call_with_retry(lambda: client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description},
                ],
                temperature=0,
            ))
            content = response.choices[0].message.content.strip()
            content = re.sub(r'^```json|```$', '', content, flags=re.MULTILINE).strip()
            analysis = json.loads(content)
            
            list_fields = ["required_skills", "preferred_skills", "key_responsibilities"]
            for field in list_fields:
                if analysis.get(field) is None:
                    analysis[field] = []

            return AnalyzedJob(
                id=raw_job.get("id", ""),
                title=raw_job.get("title", ""),
                company=raw_job.get("company", ""),
                location=raw_job.get("location", ""),
                description_length=len(description),
                redirect_url=raw_job.get("redirect_url", ""),
                salary_min=raw_job.get("salary_min"),
                salary_max=raw_job.get("salary_max"),
                **analysis,
            )

        except (json.JSONDecodeError, Exception) as e:
            last_error = e
            continue

    raise ValueError(f"Failed to analyze job '{raw_job.get('title')}' after {max_retries + 1} attempts: {last_error}")