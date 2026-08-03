export interface Basics {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  summary: string | null;
}

export interface Experience {
  company: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
  bullets: string[];
}

export interface Project {
  name: string;
  description: string | null;
  technologies: string[];
  bullets: string[];
  link: string | null;
}

export interface VerificationFlag {
  field_path: string;
  value: string;
  match_score: number;
  flagged: boolean;
}

export interface VerifiedResume {
  parsed: {
    basics: Basics;
    skills: string[];
    experience: Experience[];
    education: { institution: string; degree: string | null; field: string | null; graduation_date: string | null }[];
    projects: Project[];
    raw_text: string;
  };
  flags: VerificationFlag[];
  flagged_count: number;
}

export interface ScoreBreakdown {
  semantic_similarity: number;
  skill_overlap: number;
  matched_skills: string[];
  missing_skills: string[];
  experience_match: number;
  location_match: number;
  data_completeness: number;
  seniority_penalty_applied: boolean;
}

export interface RankedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  redirect_url: string;
  required_skills: string[];
  preferred_skills: string[];
  seniority_level: string | null;
  min_experience_years: number | null;
  employment_type: string | null;
  key_responsibilities: string[];
  salary_min: number | null;
  salary_max: number | null;
  match_score: number;
  score_breakdown: ScoreBreakdown;
}

export interface JobSearchRequest {
  user_id: string;
  role: string;
  locations: string[];
  salary_min?: number | null;
  salary_max?: number | null;
  remote_ok?: boolean | null;
}

export interface JobSearchResponse {
  ranked_jobs: RankedJob[];
  explanations: Record<string, string>;
  preferences: Record<string, unknown>;
  iteration: number;
  _session_id: string;
  __interrupt__?: unknown[];
}

export interface JobResumeRequest {
  session_id: string;
  approved: boolean;
  updated_preferences?: Record<string, unknown>;
}