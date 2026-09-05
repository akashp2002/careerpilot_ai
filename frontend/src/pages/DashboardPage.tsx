import { useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadResume } from "../api/resumeApi";
import { getProfileStatus } from "../api/profileApi";
import { searchJobsStream } from "../api/jobsApi";
import { useAuth } from "../context/AuthContext";
import { useSession } from "../context/SessionContext";
import type { ProfileStatus } from "../api/profileApi";
import type { JobSearchResponse } from "../api/types";
import TagInput from "../components/TagInput";
import "./DashboardPage.css";

export default function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { logout } = useAuth();
  const { setSessionId } = useSession();

  // ── Profile status query ──
  const { data: profile, isLoading: profileLoading } = useQuery<ProfileStatus>({
    queryKey: ["profileStatus"],
    queryFn: getProfileStatus,
  });

  // ── Upload state ──
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showUploader, setShowUploader] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: uploadResume,
    onSuccess: () => {
      setFile(null);
      setShowUploader(false);
      queryClient.invalidateQueries({ queryKey: ["profileStatus"] });
    },
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === "application/pdf") {
      setFile(dropped);
    }
  }, []);

  const handleUpload = () => {
    if (file) uploadMutation.mutate(file);
  };

  // ── Search state ──
  const [role, setRole] = useState("");
  const [locations, setLocations] = useState<string[]>([]);
  const [salaryMin, setSalaryMin] = useState("");
  const [remoteOk, setRemoteOk] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (locations.length === 0) return;

    setIsSearching(true);
    setSearchError(null);
    setProgressMessage("Starting search...");

    try {
      const result: JobSearchResponse = await searchJobsStream(
        {
          user_id: "unused",
          role,
          locations,
          salary_min: salaryMin ? Number(salaryMin) : null,
          remote_ok: remoteOk,
        },
        (progress) => setProgressMessage(progress.message)
      );

      setSessionId(result._session_id);
      navigate("/review", { state: { result } });
    } catch {
      setSearchError("Search failed. Try again in a moment.");
      setIsSearching(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  // Decide whether to show the uploader by default
  const needsUpload = !profileLoading && !profile?.has_profile;

  // ── Render ──
  return (
    <div className="dashboard">
      <div className="dashboard-top-bar">
        <button onClick={handleLogout} className="sign-out-btn">
          Sign out
        </button>
      </div>

      <div className="dashboard-content">
        {/* Loading skeleton */}
        {profileLoading && (
          <div className="skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
          </div>
        )}

        {/* ── State A: No resume yet ── */}
        {needsUpload && !showUploader && (
          <UploadSection
            file={file}
            setFile={setFile}
            isDragging={isDragging}
            setIsDragging={setIsDragging}
            handleDrop={handleDrop}
            handleUpload={handleUpload}
            mutation={uploadMutation}
            title="Upload your resume"
            subtitle="We'll read your skills, experience, and projects to find roles worth your time."
          />
        )}

        {/* ── State B: Has resume ── */}
        {!profileLoading && profile?.has_profile && (
          <>
            {/* Profile summary */}
            <div className="profile-card">
              <div className="profile-info">
                <h2>{profile.name || "Your Profile"}</h2>
                <p className="profile-meta">
                  {profile.experience_count} experience{profile.experience_count !== 1 ? "s" : ""} on file
                </p>
                {profile.skills && profile.skills.length > 0 && (
                  <div className="profile-skills">
                    {profile.skills.map((skill) => (
                      <span key={skill} className="skill-chip">{skill}</span>
                    ))}
                  </div>
                )}
              </div>
              <button
                className="update-resume-btn"
                onClick={() => setShowUploader((v) => !v)}
              >
                {showUploader ? "Cancel" : "Update resume"}
              </button>
            </div>

            {/* Inline uploader (toggled) */}
            {showUploader && (
              <UploadSection
                file={file}
                setFile={setFile}
                isDragging={isDragging}
                setIsDragging={setIsDragging}
                handleDrop={handleDrop}
                handleUpload={handleUpload}
                mutation={uploadMutation}
                title="Update your resume"
                subtitle="Upload a new PDF to refresh your profile."
              />
            )}

            <div className="section-divider">job search</div>

            {/* Search form */}
            <form className="search-section" onSubmit={handleSearch}>
              <p className="eyebrow mono">FIND ROLES</p>
              <h2>What are you looking for?</h2>
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

              {searchError && <div className="error-banner">{searchError}</div>}

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
          </>
        )}
      </div>
    </div>
  );
}

/* ── Extracted Upload UI ── */
interface UploadSectionProps {
  file: File | null;
  setFile: (f: File | null) => void;
  isDragging: boolean;
  setIsDragging: (v: boolean) => void;
  handleDrop: (e: React.DragEvent) => void;
  handleUpload: () => void;
  mutation: ReturnType<typeof useMutation<any, any, File, any>>;
  title: string;
  subtitle: string;
}

function UploadSection({
  file, setFile, isDragging, setIsDragging,
  handleDrop, handleUpload, mutation, title, subtitle,
}: UploadSectionProps) {
  return (
    <div className="upload-section">
      <p className="eyebrow mono">CANDIDATE PROFILE</p>
      <h1>{title}</h1>
      <p className="subtitle">{subtitle}</p>

      <div
        className={`dropzone ${isDragging ? "dropzone--active" : ""} ${file ? "dropzone--filled" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {file ? (
          <>
            <p className="file-name mono">{file.name}</p>
            <p className="file-meta">{(file.size / 1024).toFixed(0)} KB · ready to analyze</p>
          </>
        ) : (
          <>
            <p>Drag your PDF here, or</p>
            <label className="browse-label">
              browse files
              <input
                type="file"
                accept="application/pdf"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </>
        )}
      </div>

      {mutation.isError && (
        <div className="error-banner">
          {(mutation.error as any)?.response?.data?.detail ??
            "Something went wrong reading that file. Try again."}
        </div>
      )}

      <button
        className="submit-btn"
        disabled={!file || mutation.isPending}
        onClick={handleUpload}
      >
        {mutation.isPending ? "Analyzing resume…" : "Upload & Analyze"}
      </button>
    </div>
  );
}
