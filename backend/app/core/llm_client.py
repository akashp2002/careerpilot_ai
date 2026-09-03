import os
import json
import re
import time
from groq import Groq, RateLimitError
from google import genai
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_FALLBACK_MODEL = "gemini-flash-latest"


def _is_daily_quota_error(error: Exception) -> bool:
    msg = str(error)
    return "tokens per day" in msg or "TPD" in msg


def get_structured_completion(
    system_prompt: str,
    user_content: str,
    groq_model: str,
    temperature: float = 0,
    max_completion_tokens: int = 2048,
    max_groq_retries: int = 3,
    base_delay: float = 2.0,
) -> str:
    """
    Calls Groq with backoff retry for transient (per-minute) rate limits.
    Falls back to Gemini if: the daily quota is exhausted (no point
    retrying), OR Groq retries are exhausted without success (sustained
    limiting Groq itself couldn't recover from in time).
    """
    last_error = None

    for attempt in range(max_groq_retries + 1):
        try:
            response = groq_client.chat.completions.create(
                model=groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
                reasoning_effort="low",
                include_reasoning=False,
                max_completion_tokens=max_completion_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            last_error = e
            if _is_daily_quota_error(e):
                print(f"[LLMClient] Groq daily quota exhausted - skipping retries, falling back to Gemini")
                break  # no point retrying a daily cap - go straight to fallback

            if attempt == max_groq_retries:
                print(f"[LLMClient] Groq retries exhausted - falling back to Gemini")
                break

            delay = base_delay * (2 ** attempt)
            print(f"[LLMClient] Groq rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_groq_retries})")
            time.sleep(delay)

    # Fallback path - either daily quota hit, or all Groq retries exhausted
    print(f"[LLMClient] Using Gemini fallback ({GEMINI_FALLBACK_MODEL})")
    gemini_response = gemini_client.models.generate_content(
        model=GEMINI_FALLBACK_MODEL,
        contents=f"{system_prompt}\n\n{user_content}",
        config={"temperature": temperature},
    )
    return gemini_response.text.strip()