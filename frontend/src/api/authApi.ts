import { apiClient } from "./client";

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  // OAuth2PasswordRequestForm requires form data
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const response = await apiClient.post<AuthResponse>("/api/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
}

export async function registerUser(email: string, password: string): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/api/auth/register", {
    email,
    password,
  });
  return response.data;
}
