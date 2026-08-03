import time
from groq import RateLimitError


def call_with_retry(fn, max_retries: int = 3, base_delay: float = 2.0):
    """
    Calls a Groq-invoking function with exponential backoff on rate limits.
    fn should be a zero-arg callable (use a lambda or functools.partial).
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"[GroqRetry] rate limited, waiting {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)