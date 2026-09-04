"""
Input guardrails for CareerPilot AI.

Three layers of protection before any user-supplied text reaches an LLM:

1. PDF Upload Validation   — file size, page count, meaningful text check
2. Prompt Injection Detection — pattern-based detection of common injection attacks
3. Search Input Sanitization — length/character limits on search preferences
"""

import re
from fastapi import HTTPException


# ── Constants ──────────────────────────────────────────────────────────────────

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_PDF_PAGES = 15
MIN_RESUME_CHARS = 100                 # shorter than this is almost certainly not a resume
MAX_RESUME_CHARS = 50_000              # truncate beyond this to bound LLM input cost

MAX_ROLE_LENGTH = 100
MAX_LOCATION_LENGTH = 80
MAX_LOCATIONS_COUNT = 5
MAX_SALARY = 100_000_000               # 100M — anything above is clearly bogus

# ── Prompt Injection Detection ─────────────────────────────────────────────────

# Patterns that indicate someone is trying to override the system prompt.
# These are case-insensitive and designed to catch the most common vectors
# while minimizing false positives on legitimate resume text.
_INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|context)",
    r"ignore\s+(everything|anything)\s+(above|before|previously)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?|context)",

    # Role hijacking
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an|if)\s+",
    r"pretend\s+(you\s+are|to\s+be)\s+",
    r"your\s+new\s+(role|instructions?|task)\s+(is|are)",
    r"switch\s+to\s+.{0,20}\s+mode",

    # System prompt extraction
    r"(print|output|reveal|show|display|repeat)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)",

    # Output manipulation
    r"return\s+only\s+the\s+(following|word|phrase|text)",
    r"(respond|reply|answer)\s+with\s+only",
    r"output\s+(exactly|only|nothing\s+but)",

    # Delimiter/fence attacks
    r"<\s*/?\s*system\s*>",
    r"\[/?INST\]",
    r"```\s*system",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<<\s*SYS\s*>>",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> list[str]:
    """
    Scans text for prompt injection patterns.
    Returns a list of matched pattern descriptions (empty if clean).
    """
    matches = []
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return matches


def check_prompt_injection(text: str, source: str = "input") -> None:
    """
    Raises HTTPException 422 if prompt injection is detected.
    `source` is used in the error message for debugging (e.g. "resume", "role").
    """
    matches = detect_prompt_injection(text)
    if matches:
        print(f"[Guardrail] Prompt injection detected in {source}: {len(matches)} pattern(s) matched")
        raise HTTPException(
            status_code=422,
            detail=f"Your {source} contains text patterns that look like prompt injection attempts. "
                   f"Please remove any instructions directed at the AI system and try again."
        )


# ── PDF Upload Validation ──────────────────────────────────────────────────────

def validate_pdf_size(content_bytes: bytes) -> None:
    """Check file size before writing to disk."""
    if len(content_bytes) > MAX_PDF_SIZE_BYTES:
        size_mb = len(content_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"PDF is too large ({size_mb:.1f} MB). Maximum allowed is {MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB."
        )


def validate_pdf_pages(page_count: int) -> None:
    """Check page count after opening the PDF."""
    if page_count > MAX_PDF_PAGES:
        raise HTTPException(
            status_code=400,
            detail=f"PDF has {page_count} pages. Maximum allowed is {MAX_PDF_PAGES}. "
                   f"Please upload a concise resume."
        )


def validate_resume_text(raw_text: str) -> str:
    """
    Validates and sanitizes extracted resume text:
    - Checks minimum length (is this actually a resume?)
    - Truncates excessively long text to bound LLM costs
    - Runs prompt injection detection
    Returns the (possibly truncated) text.
    """
    stripped = raw_text.strip()

    if not stripped:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from PDF. It may be a scanned image."
        )

    if len(stripped) < MIN_RESUME_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"Extracted text is too short ({len(stripped)} characters). "
                   f"This doesn't look like a complete resume."
        )

    # Truncate to bound LLM input size
    if len(stripped) > MAX_RESUME_CHARS:
        print(f"[Guardrail] Resume text truncated from {len(stripped)} to {MAX_RESUME_CHARS} chars")
        stripped = stripped[:MAX_RESUME_CHARS]

    # Check for prompt injection
    check_prompt_injection(stripped, source="resume")

    return stripped


# ── Search Input Sanitization ──────────────────────────────────────────────────

def validate_search_inputs(role: str, locations: list[str], salary_min: int | None, salary_max: int | None) -> None:
    """
    Validates and sanitizes job search request fields.
    Raises HTTPException on invalid input.
    """
    # Role validation
    if not role or not role.strip():
        raise HTTPException(status_code=400, detail="Role is required.")

    if len(role) > MAX_ROLE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Role is too long ({len(role)} chars). Maximum is {MAX_ROLE_LENGTH}."
        )

    check_prompt_injection(role, source="role")

    # Location validation
    if not locations:
        raise HTTPException(status_code=400, detail="At least one location is required.")

    if len(locations) > MAX_LOCATIONS_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Too many locations ({len(locations)}). Maximum is {MAX_LOCATIONS_COUNT}."
        )

    for loc in locations:
        if len(loc) > MAX_LOCATION_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Location '{loc[:30]}...' is too long. Maximum is {MAX_LOCATION_LENGTH} characters."
            )
        check_prompt_injection(loc, source="location")

    # Salary validation
    if salary_min is not None and salary_min < 0:
        raise HTTPException(status_code=400, detail="Minimum salary cannot be negative.")

    if salary_max is not None and salary_max < 0:
        raise HTTPException(status_code=400, detail="Maximum salary cannot be negative.")

    if salary_min is not None and salary_min > MAX_SALARY:
        raise HTTPException(status_code=400, detail=f"Minimum salary {salary_min} is unrealistically high.")

    if salary_max is not None and salary_max > MAX_SALARY:
        raise HTTPException(status_code=400, detail=f"Maximum salary {salary_max} is unrealistically high.")

    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise HTTPException(status_code=400, detail="Minimum salary cannot exceed maximum salary.")
