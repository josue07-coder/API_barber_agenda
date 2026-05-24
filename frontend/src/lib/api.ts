import axios, { AxiosError } from "axios";
import type { ApiErrorBody } from "@/types/api";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";
export const TOKEN_STORAGE_KEY = "barber_agenda_token";

export class ApiClientError extends Error {
  status: number;
  body?: ApiErrorBody;

  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export const api = axios.create({
  baseURL: API_URL,
  timeout: 20_000
});

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }

    const message =
      error.response?.data?.message ??
      error.response?.data?.error_code ??
      error.message ??
      "Error inesperado";

    return Promise.reject(
      new ApiClientError(error.response?.status ?? 0, message, error.response?.data)
    );
  }
);
