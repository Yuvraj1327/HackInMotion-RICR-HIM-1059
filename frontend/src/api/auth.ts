import { apiClient } from "@/api/client";
import type { AuthResponse, LoginInput, RegisterInput } from "@/types/api";

/**
 * Signup goes through the backend's /auth/register endpoint because it
 * both creates the Supabase Auth user AND writes the `profiles` row
 * (business_name) via the service-role key in one step. Login uses the
 * Supabase JS client directly (see hooks/useAuth.tsx) since it needs no
 * extra backend logic - that keeps the "React -> Supabase Auth -> Access
 * Token" flow as direct as possible for the common case.
 */
export async function registerAccount(input: RegisterInput): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", input);
  return data;
}

export async function loginViaBackend(input: LoginInput): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", input);
  return data;
}

/**
 * "Continue as Guest" - deliberately a DIFFERENT endpoint from
 * `registerAccount`. `/auth/register` calls Supabase's public sign-up
 * flow, which sends a confirmation email and is subject to Supabase's
 * per-project sign-up email rate limit; a guest button clicked
 * repeatedly during a demo would quickly trip "email rate limit
 * exceeded". `/auth/guest` instead uses the backend's admin-provisioned
 * account path, which never sends an email and isn't subject to that
 * limit, while still returning a real Supabase-issued session.
 */
export async function guestLogin(): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/guest");
  return data;
}