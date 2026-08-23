import os
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from rapidfuzz import fuzz
import torch


_model = None

DEBUG_SKILL_MATCHING = os.getenv("DEBUG_SKILL_MATCHING", "false").lower() == "true"

SKILL_MATCH_THRESHOLD = 0.55  # cosine similarity threshold for semantic skill matching
# NOTE: this threshold is a starting guess, not calibrated. Set
# DEBUG_SKILL_MATCHING=true and check real req_skill vs candidate_skill
# scores against cases you know should/shouldn't match, then adjust.


def get_model():
    """Lazy-load the model once, reused across calls."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _model


def build_candidate_text(candidate_profile: dict) -> str:
    """Flattens the candidate profile into a single text blob for embedding."""
    parts = []

    skills = candidate_profile.get("skills", [])
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    for exp in candidate_profile.get("experience", []):
        title = exp.get("title", "")
        bullets = " ".join(exp.get("bullets", []))
        parts.append(f"{title}: {bullets}")

    for proj in candidate_profile.get("projects", []):
        name = proj.get("name", "")
        desc = proj.get("description", "") or ""
        techs = ", ".join(proj.get("technologies", []))
        parts.append(f"Project {name}: {desc} ({techs})")

    return " | ".join(parts)


def build_job_text(job: dict) -> str:
    """Flattens an analyzed job into a single text blob for embedding."""
    parts = [job.get("title", "")]

    if job.get("required_skills"):
        parts.append("Required: " + ", ".join(job["required_skills"]))
    if job.get("preferred_skills"):
        parts.append("Preferred: " + ", ".join(job["preferred_skills"]))
    if job.get("key_responsibilities"):
        parts.append(" ".join(job["key_responsibilities"]))

    return " | ".join(parts)


def compute_skill_overlap(
    candidate_skills: list[str],
    required_skills: list[str],
    description_length: int = 0,
    candidate_skill_embeddings=None,
) -> tuple[float, list[str], list[str]]:
    """
    Returns (overlap_ratio, matched_skills, missing_skills).
    Uses semantic embedding similarity, not string matching - so
    "LangGraph" correctly matches against a required skill phrased as
    "AI agent orchestration framework" even though they share no
    common substring.
    """
    if not required_skills:
        ratio = 0.5 if description_length >= 500 else 1.0
        return ratio, [], []

    if not candidate_skills or candidate_skill_embeddings is None:
        return 0.0, [], required_skills

    model = get_model()
    required_embeddings = model.encode(required_skills, convert_to_tensor=True)
    similarity_matrix = cos_sim(required_embeddings, candidate_skill_embeddings)
    matched, missing = [], []
    for i, req_skill in enumerate(required_skills):
        best_score = float(torch.max(similarity_matrix[i]))

        if DEBUG_SKILL_MATCHING:
            best_idx = int(torch.argmax(similarity_matrix[i]))
            best_candidate_skill = candidate_skills[best_idx]
            print(
                f"[skill-match] required={req_skill!r} "
                f"best_candidate={best_candidate_skill!r} "
                f"score={best_score:.3f} "
                f"{'MATCH' if best_score >= SKILL_MATCH_THRESHOLD else 'no match'}"
            )

        if best_score >= SKILL_MATCH_THRESHOLD:
            matched.append(req_skill)
        else:
            missing.append(req_skill)

    ratio = len(matched) / len(required_skills)
    return ratio, matched, missing


def estimate_candidate_experience_years(experience: list[dict], projects: list[dict] = None) -> float:
    """
    Rough experience proxy. Real work experience entries count fully.
    For freshers with no work experience, substantial projects count
    as partial credit rather than zeroing out entirely.
    """
    if experience:
        return float(len(experience))

    projects = projects or []
    return min(len(projects) * 0.5, 2.0)  # capped credit, avoids overstating a fresher as "senior"


SENIOR_KEYWORDS = ["senior", "sr.", "sr ", "lead", "principal", "staff", "architect"]
ENTRY_KEYWORDS = ["junior", "jr.", "entry", "graduate", "intern", "trainee", "fresher"]


def infer_seniority_from_title(title: str) -> str | None:
    """Fallback signal when structured extraction has no seniority_level/min_experience_years."""
    title_lower = title.lower()
    if any(kw in title_lower for kw in SENIOR_KEYWORDS):
        return "senior"
    if any(kw in title_lower for kw in ENTRY_KEYWORDS):
        return "entry"
    return None


def check_experience_match(candidate_years: float, min_required: int | None, job_title: str = "", description_length: int = 0) -> float:
    if min_required is not None:
        if min_required <= 0:
            return 1.0
        if candidate_years >= min_required:
            return 1.0
        if min_required <= 2:
            return max(0.4, candidate_years / min_required)
        return max(0.0, candidate_years / min_required)

    # min_required is unknown - don't default to a free pass.
    # Fall back to title-based seniority as a cheap signal, especially
    # useful when the description was truncated before reaching the
    # experience requirement line.
    inferred = infer_seniority_from_title(job_title)

    if inferred == "senior" and candidate_years < 2:
        return 0.25  # explicit senior title + fresher-level experience: real mismatch
    if inferred == "entry":
        return 1.0

    # No title signal either - genuinely unknown, stay neutral rather than perfect
    if description_length >= 500:
        return 0.5  # likely truncated
    else:
        return 0.8  # probably complete but just doesn't mention experience


def check_location_match(candidate_location: str, job_location: str, preferences: dict) -> float:
    pref_locations = [loc.lower() for loc in (preferences.get("locations") or [])]
    job_loc = (job_location or "").lower()

    if preferences.get("remote_ok") and "remote" in job_loc:
        return 1.0
    if not pref_locations or not job_loc:
        return 0.5  # unknown, neutral

    # Best match across all acceptable locations - job only needs to
    # satisfy ONE of the candidate's preferred locations, not all
    best_score = 0.0
    for pref in pref_locations:
        if pref in job_loc:
            return 1.0
        score = fuzz.partial_ratio(pref, job_loc) / 100
        best_score = max(best_score, score)

    return best_score


def compute_data_completeness(job: dict) -> float:
    """Fraction of key structured fields that were actually extracted."""
    fields_present = 0
    total_fields = 3

    if job.get("required_skills"):
        fields_present += 1
    if job.get("min_experience_years") is not None:
        fields_present += 1
    if job.get("seniority_level"):
        fields_present += 1

    return fields_present / total_fields


def meets_salary_requirement(job: dict, preferences: dict) -> bool:
    """
    Hard filter: excludes jobs whose salary is clearly below the
    candidate's stated minimum. Jobs with no salary data are kept
    (undisclosed, not necessarily disqualifying).
    """
    pref_min = preferences.get("salary_min")
    if not pref_min:
        return True  # no preference set, nothing to filter on

    job_max = job.get("salary_max")
    job_min = job.get("salary_min")

    # If the job discloses a max and it's below what the candidate wants, exclude
    if job_max is not None and job_max < pref_min:
        return False
    # If only a min is disclosed and it's well below preference, exclude
    if job_max is None and job_min is not None and job_min < pref_min:
        return False

    return True


def score_jobs(candidate_profile: dict, analyzed_jobs: list[dict], preferences: dict = None) -> list[dict]:
    if not analyzed_jobs:
        return []

    preferences = preferences or {}

    # Hard-filter out jobs that clearly don't meet salary requirements
    eligible_jobs = [job for job in analyzed_jobs if meets_salary_requirement(job, preferences)]

    if not eligible_jobs:
        return []  # nothing meets the bar - real, honest empty result

    model = get_model()

    candidate_skills = candidate_profile.get("skills", [])
    candidate_skill_embeddings = model.encode(candidate_skills, convert_to_tensor=True) if candidate_skills else None

    candidate_text = build_candidate_text(candidate_profile)
    job_texts = [build_job_text(job) for job in eligible_jobs]

    candidate_embedding = model.encode(candidate_text, convert_to_tensor=True)
    job_embeddings = model.encode(job_texts, convert_to_tensor=True)
    semantic_scores = cos_sim(candidate_embedding, job_embeddings)[0]

    candidate_years = estimate_candidate_experience_years(
        candidate_profile.get("experience", []),
        candidate_profile.get("projects", []),
    )
    candidate_location = candidate_profile.get("basics", {}).get("location", "")
    candidate_is_fresher = not candidate_profile.get("experience")

    scored_jobs = []
    # FIX: iterate eligible_jobs (what semantic_scores was actually computed
    # against), not analyzed_jobs - previously these could be different
    # lengths whenever any job got salary-filtered, silently pairing jobs
    # with the wrong semantic score.
    for job, sem_score in zip(eligible_jobs, semantic_scores):
        semantic = float(sem_score)
        description_length = job.get("description_length", 0)

        skill_overlap, matched_skills, missing_skills = compute_skill_overlap(
            candidate_skills,
            job.get("required_skills", []),
            description_length,
            candidate_skill_embeddings,
        )

        experience = check_experience_match(
            candidate_years, job.get("min_experience_years"), job.get("title", ""), description_length
        )
        location = check_location_match(candidate_location, job.get("location", ""), preferences)

        composite = (
            semantic * 0.50 +
            skill_overlap * 0.30 +
            experience * 0.10 +
            location * 0.10
        )

        # Dampen by data completeness: a listing missing most structured
        # fields shouldn't compete on equal footing with a fully-analyzed one
        completeness = compute_data_completeness(job)
        composite *= (0.7 + 0.3 * completeness)  # ranges 0.7x (nothing extracted) to 1.0x (fully extracted)

        # Hard penalty for a clear, title-visible seniority mismatch -
        # title text is always available (never truncated), so this signal
        # is trustworthy even when everything else about the listing is thin
        inferred_seniority = infer_seniority_from_title(job.get("title", ""))
        if inferred_seniority == "senior" and candidate_is_fresher:
            composite *= 0.5  # direct cut, not diluted into a 10%-weighted average

        job_with_score = {
            **job,
            "match_score": round(composite * 100, 2),
            "score_breakdown": {
                "semantic_similarity": round(semantic * 100, 2),
                "skill_overlap": round(skill_overlap * 100, 2),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "experience_match": round(experience * 100, 2),
                "location_match": round(location * 100, 2),
                "data_completeness": round(completeness * 100, 2),
                "seniority_penalty_applied": inferred_seniority == "senior" and candidate_is_fresher,
            },
        }
        scored_jobs.append(job_with_score)

    scored_jobs.sort(key=lambda j: j["match_score"], reverse=True)
    return scored_jobs