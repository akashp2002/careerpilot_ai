import { apiClient } from "./client";
import type { VerifiedResume } from "./types";

export async function uploadResume(file: File): Promise<VerifiedResume> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<VerifiedResume>("/api/resume/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}