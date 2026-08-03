from pydantic import BaseModel, Field
from typing import Optional


class AnalyzedJob(BaseModel):
    id: str
    title: str
    company: str
    location: str
    redirect_url: str

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    seniority_level: Optional[str] = None       # e.g. "entry", "mid", "senior"
    min_experience_years: Optional[int] = None
    employment_type: Optional[str] = None        # e.g. "full-time", "contract"
    key_responsibilities: list[str] = Field(default_factory=list)
    description_length: int = 0

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None