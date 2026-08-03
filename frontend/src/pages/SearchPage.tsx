import { useState } from "react";
import { useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { searchJobs } from "../api/jobsApi";
import { useSession } from "../context/SessionContext";
import type { JobSearchResponse } from "../api/types";
import "./SearchPage.css";

export default function SearchPage() {
  const navigate = useNavigate();
  const { setSessionId } = useSession();

  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [salaryMin, setSalaryMin] = useState("");
  const [remoteOk, setRemoteOk] = useState(false);

  const mutation = useMutation({
    mutationFn: searchJobs,
    onSuccess: (data: JobSearchResponse) => {
      setSessionId(data._session_id);
      navigate("/review", { state: { result: data } });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      user_id: "demo_user",
      role,
      location,
      salary_min: salaryMin ? Number(salaryMin) : null,
      remote_ok: remoteOk,
    });
  };

  return (
    <div className="search-page">
      <form className="search-card" onSubmit={handleSubmit}>
        <p className="eyebrow mono">JOB SEARCH</p>
        <h1>What are you looking for?</h1>
        <p className="subtitle">
          We'll search across multiple job sources and rank results against your profile.
        </p>

        <label className="field-label">Role</label>
        <input
          className="text-input"
          placeholder="e.g. Backend Engineer"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
        />

        <label className="field-label">Location</label>
        <input
          className="text-input"
          placeholder="e.g. Bangalore"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          required
        />

        <label className="field-label">Minimum salary (optional)</label>
        <input
          className="text-input"
          type="number"
          placeholder="e.g. 600000"
          value={salaryMin}
          onChange={(e) => setSalaryMin(e.target.value)}
        />

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={remoteOk}
            onChange={(e) => setRemoteOk(e.target.checked)}
          />
          Open to remote roles
        </label>

        {mutation.isError && (
          <div className="error-banner">
            {(mutation.error as any)?.response?.data?.detail ??
              "Search failed. Try again in a moment."}
          </div>
        )}

        <button className="submit-btn" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Searching…" : "Find matching jobs"}
        </button>
      </form>
    </div>
  );
}