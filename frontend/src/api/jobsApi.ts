import { apiClient } from "./client";
import type { JobSearchRequest, JobSearchResponse, JobResumeRequest } from "./types";

export async function searchJobs(request: JobSearchRequest): Promise<JobSearchResponse> {
  const response = await apiClient.post<JobSearchResponse>("/api/jobs/search", request);
  return response.data;
}

export async function resumeJobSearch(request: JobResumeRequest): Promise<JobSearchResponse> {
  const response = await apiClient.post<JobSearchResponse>("/api/jobs/resume", request);
  return response.data;
}