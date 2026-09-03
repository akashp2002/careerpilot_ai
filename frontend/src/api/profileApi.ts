import { apiClient } from "./client";

export interface ProfileStatus {
  has_profile: boolean;
  name?: string | null;
  skills?: string[];
  experience_count?: number;
}

export async function getProfileStatus(): Promise<ProfileStatus> {
  const response = await apiClient.get<ProfileStatus>("/api/profile/status");
  return response.data;
}
