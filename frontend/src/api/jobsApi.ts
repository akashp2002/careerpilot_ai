import { apiClient } from "./client";
import type { JobSearchRequest, JobSearchResponse, JobResumeRequest } from "./types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

export async function searchJobs(request: JobSearchRequest): Promise<JobSearchResponse> {
  const response = await apiClient.post<JobSearchResponse>("/api/jobs/search", request);
  return response.data;
}

export async function resumeJobSearch(request: JobResumeRequest): Promise<JobSearchResponse> {
  const response = await apiClient.post<JobSearchResponse>("/api/jobs/resume", request);
  return response.data;
}

export interface StreamProgressEvent {
  type: "progress";
  node: string;
  message: string;
}

export interface StreamCompleteEvent {
  type: "complete";
  result: JobSearchResponse;
}

type StreamEvent = StreamProgressEvent | StreamCompleteEvent;

export async function searchJobsStream(
  request: JobSearchRequest,
  onProgress: (event: StreamProgressEvent) => void
): Promise<JobSearchResponse> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBaseUrl}/api/jobs/search/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(request),
  });

  if (!response.body) throw new Error("No response stream available");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: JobSearchResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const event: StreamEvent = JSON.parse(line.slice(6));

      if (event.type === "progress") {
        onProgress(event);
      } else if (event.type === "complete") {
        finalResult = event.result;
      }
    }
  }

  if (!finalResult) throw new Error("Stream ended without a result");
  return finalResult;
}