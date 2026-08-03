from pydantic import BaseModel, Field
from typing import Optional


class Basics(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    graduation_date: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    link: Optional[str] = None


class ParsedResume(BaseModel):
    basics: Basics
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    raw_text: str

class VerificationFlag(BaseModel):
    field_path: str        # e.g. "experience[0].company"
    value: str              # the extracted value being checked
    match_score: float      # 0-100 fuzzy match confidence against raw_text
    flagged: bool            # True if below confidence threshold

class VerifiedResume(BaseModel):
    parsed: ParsedResume
    flags: list[VerificationFlag] = Field(default_factory=list)
    flagged_count: int = 0

class JobSearchRequest(BaseModel):
    user_id: str = "demo_user"
    role: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    remote_ok: Optional[bool] = None