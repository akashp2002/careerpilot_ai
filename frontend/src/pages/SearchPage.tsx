import { useState } from "react";
import { useNavigate } from "react-router";
import { searchJobsStream } from "../api/jobsApi";
import { useSession } from "../context/SessionContext";
import type { JobSearchResponse } from "../api/types";
import TagInput from "../components/TagInput";
import "./SearchPage.css";

export default function SearchPage() {
  const navigate = useNavigate();
  const { setSessionId } = useSession();

  const [role, setRole] = useState("");
  const [locations, setLocations] = useState<string[]>([]);
  const [salaryMin, setSalaryMin] = useState("");
  const [remoteOk, setRemoteOk] = useState(false);

  const [isSearching, setIsSearching] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (locations.length === 0) return;

    setIsSearching(true);
    setError(null);
    setProgressMessage("Starting search...");

    try {
      const result: JobSearchResponse = await searchJobsStream(
        {
          user_id: "demo_user",
          role,
          locations,
          salary_min: salaryMin ? Number(salaryMin) : null,
          remote_ok: remoteOk,
        },
        (progress) => setProgressMessage(progress.message)
      );

      setSessionId(result._session_id);
      navigate("/review", { state: { result } });
    } catch (err) {
      setError("Search failed. Try again in a moment.");
      setIsSearching(false);
    }
  };

  return (
    <div className="search-page">
      <form className="search-card" onSubmit={handleSubmit}>
        <p className="eyebrow mono">JOB SEARCH</p>
        <h1>What are you looking for?</h1>
        <p className="subtitle">
          We'll search across multiple job sources and rank results against your profile.
        </p>

        <div className="field-group">
          <label className="field-label">Role</label>
          <input
            className="text-input"
            placeholder="e.g. Backend Engineer"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
            disabled={isSearching}
          />

          <label className="field-label">Locations</label>
          <TagInput
            tags={locations}
            onChange={setLocations}
            placeholder="e.g. Bangalore, Remote"
          />
        </div>

        <div className="field-group field-group--optional">
          <p className="field-group-heading">Preferences</p>

          <label className="field-label">Minimum salary</label>
          <input
            className="text-input"
            type="number"
            placeholder="e.g. 600000"
            value={salaryMin}
            onChange={(e) => setSalaryMin(e.target.value)}
            disabled={isSearching}
          />

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={remoteOk}
              onChange={(e) => setRemoteOk(e.target.checked)}
              disabled={isSearching}
            />
            Open to remote roles
          </label>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {isSearching && (
          <div className="progress-indicator">
            <span className="progress-pulse" />
            <span className="mono">{progressMessage}</span>
          </div>
        )}

        <button className="submit-btn" type="submit" disabled={isSearching}>
          {isSearching ? "Searching…" : "Find matching jobs"}
        </button>
      </form>
    </div>
  );
}