import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { supabase } from "@/lib/supabase";
import type { ApiErrorBody } from "@/types/api";

const baseURL = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (!baseURL) {
  // eslint-disable-next-line no-console
  console.error("Missing VITE_API_BASE_URL. Copy .env.example to .env and set it.");
}

export const apiClient = axios.create({
  baseURL: baseURL ?? "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/** A normalized, user-safe error. Never exposes stack traces or raw Axios internals. */
export class ApiError extends Error {
  status: number | null;
  code: string;
  fieldErrors: Array<{ field: string; message: string }>;

  constructor(message: string, status: number | null, code: string, fieldErrors: Array<{ field: string; message: string }> = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

function normalizeError(error: AxiosError<ApiErrorBody>): ApiError {
  if (!error.response) {
    return new ApiError(
      "Unable to connect to the StockPilot server. Please check your connection and try again.",
      null,
      "network_error"
    );
  }

  const { status, data } = error.response;

  if (data && typeof data === "object" && "detail" in data) {
    if (Array.isArray(data.detail)) {
      const fieldErrors = data.detail.map((d) => ({
        field: d.loc?.[d.loc.length - 1]?.toString() ?? "field",
        message: d.msg,
      }));
      const message =
        fieldErrors.length > 0
          ? fieldErrors.map((f) => `${f.field}: ${f.message}`).join(", ")
          : "Please check the values you entered and try again.";
      return new ApiError(message, status, data.error ?? "validation_error", fieldErrors);
    }
    if (typeof data.detail === "string") {
      return new ApiError(data.detail, status, data.error ?? "error");
    }
  }

  if (status === 401) return new ApiError("Your session has expired. Please log in again.", status, "unauthorized");
  if (status === 403) return new ApiError("You don't have permission to do that.", status, "forbidden");
  if (status === 404) return new ApiError("The requested item could not be found.", status, "not_found");
  if (status >= 500) return new ApiError("Something went wrong on our end. Please try again shortly.", status, "server_error");

  return new ApiError("Something went wrong. Please try again.", status, "unknown_error");
}

// --- Attach the current Supabase access token to every request ---
apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

let isRefreshing = false;
let refreshWaiters: Array<() => void> = [];

// --- Normalize errors; on 401, try one Supabase session refresh + retry before giving up ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;

    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const { data, error: refreshError } = await supabase.auth.refreshSession();
          if (refreshError || !data.session) {
            await supabase.auth.signOut();
            window.location.assign("/login");
            return Promise.reject(normalizeError(error));
          }
        } finally {
          isRefreshing = false;
          refreshWaiters.forEach((resolve) => resolve());
          refreshWaiters = [];
        }
      } else {
        await new Promise<void>((resolve) => refreshWaiters.push(resolve));
      }

      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;
      if (token && original.headers) {
        original.headers.set("Authorization", `Bearer ${token}`);
        return apiClient(original);
      }
    }

    return Promise.reject(normalizeError(error));
  }
);
