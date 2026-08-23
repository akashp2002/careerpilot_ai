import { useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { resumeJobSearch } from "../api/jobsApi";
import { useSession } from "../context/SessionContext";
import JobCard from "../components/JobCard";
import type { JobSearchResponse } from "../api/types";
import TagInput from "../components/TagInput";
import "./ReviewPage.css";

const RESULT_STORAGE_KEY = "careerpilot_last_result";

export default function ReviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { sessionId } = useSession();

  const [result, setResultState] = useState<JobSearchResponse | undefined>(() => {
    const fromRouter = (location.state as { result: JobSearchResponse })?.result;
    if (fromRouter) return fromRouter;

    const stored = sessionStorage.getItem(RESULT_STORAGE_KEY);
    return stored ? JSON.parse(stored) : undefined;
  });

  const setResult = (data: JobSearchResponse) => {
    setResultState(data);
    sessionStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(data));
  };

  const [refineOpen, setRefineOpen] = useState(false);
  const [refineRole, setRefineRole] = useState("");
  const [refineLocations, setRefineLocations] = useState<string[]>([]);
  const [refineSalaryMin, setRefineSalaryMin] = useState("");

  const mutation = useMutation({
    mutationFn: resumeJobSearch,
    onSuccess: (data: JobSearchResponse) => {
      setResult(data);
      setRefineOpen(false);
    },
  });

  if (!result) {
    return (
      <div className="review-page">
        <p>No active search. <a href="/">Start a new search</a>.</p>
      </div>
    );
  }

  const isPaused = !!result.__interrupt__;

  const handleApprove = () => {
    if (!sessionId) {
      alert("Your session expired or wasn't found. Please start a new search.");
      navigate("/");
      return;
    }
    mutation.mutate({ session_id: sessionId, approved: true });
  };

  const handleRefine = () => {
    if (!sessionId) {
      alert("Your session expired or wasn't found. Please start a new search.");
      navigate("/");
      return;
    }

    const updated_preferences: Record<string, unknown> = {};
    if (refineRole) updated_preferences.role = refineRole;
    if (refineLocations.length > 0) {updated_preferences.locations = refineLocations;}
    if (refineSalaryMin) updated_preferences.salary_min = Number(refineSalaryMin);

    if (Object.keys(updated_preferences).length === 0) return;

    mutation.mutate({ session_id: sessionId, approved: false, updated_preferences });
  };

  return (
    <div className="review-page">
      <div className="review-topbar">
        <div>
          <p className="eyebrow mono">
            {isPaused ? "REVIEW RESULTS" : "SEARCH COMPLETE"} · ITERATION {result.iteration}
          </p>
          <h1>{result.ranked_jobs.length} matching roles found</h1>
        </div>

        {isPaused && (
          <button
            type="button"
            className="submit-btn submit-btn--secondary refine-toggle"
            onClick={() => setRefineOpen((v) => !v)}
          >
            Refine {refineOpen ? "▴" : "▾"}
          </button>
        )}
      </div>

      {isPaused && refineOpen && (
        <div className="refine-panel">
          <div className="refine-fields">
            <input
              className="text-input"
              placeholder="New role (optional)"
              value={refineRole}
              onChange={(e) => setRefineRole(e.target.value)}
            />
            <TagInput
              tags={refineLocations}
              onChange={setRefineLocations}
              placeholder="New locations (optional)"
            />
            <input
              className="text-input"
              type="number"
              placeholder="Min salary (optional)"
              value={refineSalaryMin}
              onChange={(e) => setRefineSalaryMin(e.target.value)}
            />
          </div>

          {mutation.isError && (
            <div className="error-banner">
              {(mutation.error as any)?.response?.data?.detail ?? "Couldn't refine search. Try again."}
            </div>
          )}

          <button
            className="submit-btn"
            onClick={handleRefine}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Refining…" : "Search again with these changes"}
          </button>
        </div>
      )}

      <div className="job-list">
        {result.ranked_jobs.map((job) => (
          <JobCard key={job.id} job={job} explanation={result.explanations[job.id]} />
        ))}
      </div>

      <div className="review-footer">
        {isPaused ? (
          <button className="submit-btn submit-btn--large" onClick={handleApprove} disabled={mutation.isPending}>
            Approve these results
          </button>
        ) : (
          <>
            <p className="subtitle">You approved these results. Good luck with your applications!</p>
            <button className="submit-btn submit-btn--large" onClick={() => navigate("/")}>
              Start a new search
            </button>
          </>
        )}
      </div>
    </div>
  );
}