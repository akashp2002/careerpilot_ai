import { useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { uploadResume } from "../api/resumeApi";
import "./UploadPage.css";

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const mutation = useMutation({
    mutationFn: uploadResume,
    onSuccess: () => {
      navigate("/search");
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

  const handleSubmit = () => {
    if (file) mutation.mutate(file);
  };

  return (
    <div className="upload-page">
      <div className="upload-card">
        <p className="eyebrow mono">CANDIDATE PROFILE</p>
        <h1>Upload your resume</h1>
        <p className="subtitle">
          We'll read your skills, experience, and projects to find roles worth your time.
        </p>

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
          onClick={handleSubmit}
        >
          {mutation.isPending ? "Analyzing resume…" : "Continue"}
        </button>
      </div>
    </div>
  );
}