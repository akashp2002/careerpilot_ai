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

BATCH_SYSTEM_PROMPT = """You are a job description analysis engine. You will receive
a JSON array of job listings, each with an "index" and "description". For EACH
listing, extract structured information matching this schema:

{
  "index": int,
  "required_skills": [str],
  "preferred_skills": [str],
  "seniority_level": "entry"|"mid"|"senior"|"lead"|null,
  "min_experience_years": int|null,
  "employment_type": str|null,
  "key_responsibilities": [str]
}

RULES:
- Return a JSON ARRAY with one object per input listing, in the same order.
- Each object MUST include the same "index" as its corresponding input.
- Extract ONLY what is explicitly stated or clearly implied by that listing's text.
- If a listing's description is vague/truncated, extract what you can, leave the rest null/empty.
- Return ONLY the JSON array. No markdown, no backticks, no preamble, no commentary after the array.
"""


def extract_json_array(content: str):
    """
    Parses the first valid JSON value from the model's response, ignoring
    any trailing text the model appends after it (commentary, leftover
    reasoning, etc.) - handles the "Extra data" class of parse failures
    without needing to know what the trailing content actually is.
    """
    decoder = json.JSONDecoder()
    content = content.strip()
    obj, _ = decoder.raw_decode(content)
    return obj


@traceable(name="jd_analysis_llm_call")
def analyze_job_batch(raw_jobs: list[dict], max_retries: int = 2) -> list[AnalyzedJob]:
    batch_input = [
        {"index": i, "description": job.get("description", "")}
        for i, job in enumerate(raw_jobs)
    ]

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = call_with_retry(lambda: client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": BATCH_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(batch_input)},
                ],
                temperature=0,
                reasoning_effort="low",
                include_reasoning=False,
                max_completion_tokens=2048,
            ))
            content = response.choices[0].message.content.strip()
            content = re.sub(r'^```json|```$', '', content, flags=re.MULTILINE).strip()
            analyses = extract_json_array(content)

            results = []
            for analysis in analyses:
                idx = analysis.pop("index", None)
                if idx is None or idx >= len(raw_jobs):
                    continue

                list_fields = ["required_skills", "preferred_skills", "key_responsibilities"]
                for field in list_fields:
                    if analysis.get(field) is None:
                        analysis[field] = []

                raw_job = raw_jobs[idx]
                results.append(AnalyzedJob(
                    id=raw_job.get("id", ""),
                    title=raw_job.get("title", ""),
                    company=raw_job.get("company", ""),
                    location=raw_job.get("location", ""),
                    redirect_url=raw_job.get("redirect_url", ""),
                    salary_min=raw_job.get("salary_min"),
                    salary_max=raw_job.get("salary_max"),
                    description_length=len(raw_job.get("description", "")),
                    **analysis,
                ))

            return results

        except (json.JSONDecodeError, Exception) as e:
            last_error = e
            continue

    raise ValueError(f"Failed to analyze batch of {len(raw_jobs)} jobs after {max_retries + 1} attempts: {last_error}")