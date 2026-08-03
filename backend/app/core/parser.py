import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from app.models.resume import ParsedResume
from langsmith import traceable

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a resume parsing engine. Extract information from the
provided resume text into strict JSON matching this schema:

{
  "basics": {"name": str|null, "email": str|null, "phone": str|null, "location": str|null, "summary": str|null},
  "skills": [str],
  "experience": [{"company": str, "title": str, "start_date": str|null, "end_date": str|null, "bullets": [str]}],
  "education": [{"institution": str, "degree": str|null, "field": str|null, "graduation_date": str|null}],
  "projects": [{"name": str, "description": str|null, "technologies": [str], "bullets": [str], "link": str|null}]
}

RULES:
- Extract ONLY what is explicitly present in the text. Do NOT infer, guess, or fill in missing information.
- Do NOT invent companies, dates, or skills that are not written in the text.
- If a field is not present, use null (or empty list for arrays).
- Return ONLY the JSON object. No markdown, no backticks, no preamble.
"""

def clean_text(raw_text: str) -> str:
    """Light preprocessing before LLM parsing."""
    text = re.sub(r'\n{3,}', '\n\n', raw_text)      # collapse excess blank lines
    text = re.sub(r'[ \t]{2,}', ' ', text)            # collapse repeated spaces/tabs
    text = text.strip()
    return text

@traceable(name="resume_parse_llm_call")
def parse_resume_text(raw_text: str, max_retries: int = 2) -> ParsedResume:
    cleaned = clean_text(raw_text)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": cleaned},
                ],
                temperature=0,
            )
            content = response.choices[0].message.content.strip()

            # strip accidental markdown fences, just in case
            content = re.sub(r'^```json|```$', '', content, flags=re.MULTILINE).strip()

            parsed_json = json.loads(content)
            parsed_json["raw_text"] = raw_text  # attach original for later fact-checking

            return ParsedResume(**parsed_json)

        except (json.JSONDecodeError, Exception) as e:
            last_error = e
            continue

    raise ValueError(f"Failed to parse resume after {max_retries + 1} attempts: {last_error}")