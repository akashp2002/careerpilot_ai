from rapidfuzz import fuzz
from app.models.resume import ParsedResume, VerificationFlag, VerifiedResume

CONFIDENCE_THRESHOLD = 75  # below this score, a field gets flagged


def _check_field(field_path: str, value: str, raw_text: str) -> VerificationFlag:
    """Fuzzy-match a single extracted value against the raw resume text."""
    if not value:
        return VerificationFlag(field_path=field_path, value="", match_score=100.0, flagged=False)

    score = fuzz.partial_ratio(value.lower(), raw_text.lower())
    return VerificationFlag(
        field_path=field_path,
        value=value,
        match_score=score,
        flagged=score < CONFIDENCE_THRESHOLD,
    )


def verify_resume(parsed: ParsedResume) -> VerifiedResume:
    raw_text = parsed.raw_text
    flags: list[VerificationFlag] = []

    # basics
    b = parsed.basics
    for attr in ["name", "email", "phone", "location"]:
        val = getattr(b, attr)
        if val:
            flags.append(_check_field(f"basics.{attr}", val, raw_text))

    # skills
    for i, skill in enumerate(parsed.skills):
        flags.append(_check_field(f"skills[{i}]", skill, raw_text))

    # experience
    for i, exp in enumerate(parsed.experience):
        flags.append(_check_field(f"experience[{i}].company", exp.company, raw_text))
        flags.append(_check_field(f"experience[{i}].title", exp.title, raw_text))
        if exp.start_date:
            flags.append(_check_field(f"experience[{i}].start_date", exp.start_date, raw_text))
        if exp.end_date:
            flags.append(_check_field(f"experience[{i}].end_date", exp.end_date, raw_text))
        for j, bullet in enumerate(exp.bullets):
            flags.append(_check_field(f"experience[{i}].bullets[{j}]", bullet, raw_text))

    # education
    for i, edu in enumerate(parsed.education):
        flags.append(_check_field(f"education[{i}].institution", edu.institution, raw_text))
        if edu.degree:
            flags.append(_check_field(f"education[{i}].degree", edu.degree, raw_text))
        if edu.field:
            flags.append(_check_field(f"education[{i}].field", edu.field, raw_text))

    flagged_count = sum(1 for f in flags if f.flagged)

    return VerifiedResume(parsed=parsed, flags=flags, flagged_count=flagged_count)