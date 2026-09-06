import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});