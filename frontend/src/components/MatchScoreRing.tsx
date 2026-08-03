interface MatchScoreRingProps {
  score: number;
}

export default function MatchScoreRing({ score }: MatchScoreRingProps) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color = score >= 70 ? "var(--accent)" : score >= 45 ? "var(--warning)" : "var(--danger)";

  return (
    <div className="match-ring">
      <svg width="84" height="84" viewBox="0 0 84 84">
        <circle cx="42" cy="42" r={radius} fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle
          cx="42"
          cy="42"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 42 42)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span className="match-ring-value mono">{Math.round(score)}</span>
    </div>
  );
}