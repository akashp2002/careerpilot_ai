import type { RankedJob } from "../api/types";
import MatchScoreRing from "./MatchScoreRing";
import "./JobCard.css";

interface JobCardProps {
  job: RankedJob;
  explanation?: string;
}

export default function JobCard({ job, explanation }: JobCardProps) {
  const { score_breakdown } = job;

  return (
    <div className="job-card">
      <div className="job-card-header">
        <div>
          <h3>{job.title}</h3>
          <p className="job-meta">{job.company} · {job.location}</p>
        </div>
        <MatchScoreRing score={job.match_score} />
      </div>

      {explanation && <p className="job-explanation">{explanation}</p>}

      {score_breakdown.seniority_penalty_applied && (
        <div className="job-flag">Seniority level may exceed your current experience</div>
      )}
      {score_breakdown.data_completeness < 50 && (
        <div className="job-flag job-flag--muted">Limited details available in this posting</div>
      )}

      <div className="skills-row">
        {score_breakdown.matched_skills.map((s) => (
          <span key={s} className="skill-tag skill-tag--matched mono">{s}</span>
        ))}
        {score_breakdown.missing_skills.map((s) => (
          <span key={s} className="skill-tag skill-tag--missing mono">{s}</span>
        ))}
      </div>

      <div className="job-card-footer">
        {(job.salary_min || job.salary_max) && (
          <span className="salary mono">
            ₹{job.salary_min?.toLocaleString() ?? "?"} – ₹{job.salary_max?.toLocaleString() ?? "?"}
          </span>
        )}
        <a href={job.redirect_url} target="_blank" rel="noopener noreferrer" className="view-link">
          View posting →
        </a>
      </div>
    </div>
  );
}