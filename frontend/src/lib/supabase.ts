import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!supabaseUrl || !supabaseAnonKey) {
  // eslint-disable-next-line no-console
  console.error(
    "Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY. Copy .env.example to .env and fill in your Supabase project credentials."
  );
}

/**
 * Single shared Supabase client for the whole app. Session persistence and
 * automatic access-token refresh are handled by the SDK itself
 * (persistSession + autoRefreshToken, both default to true), so once a
 * session is established (via signInWithPassword, signUp, or setSession
 * after our backend's /auth/register call) the SDK keeps the access token
 * fresh in the background.
 */
export const supabase = createClient(supabaseUrl ?? "", supabaseAnonKey ?? "", {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/**
 * Resolves once the initial session restoration (reading whatever
 * session was persisted in localStorage from a previous visit, and -
 * per the Supabase JS client's own documented behavior - refreshing it
 * first if it's already expired) has completed. Kicked off immediately
 * at module load, i.e. before React even renders.
 *
 * `apiClient`'s request interceptor awaits this before attaching a
 * token to ANY request. Without it, an API call could theoretically
 * fire (e.g. via a query library's background refetch, or any code
 * path not strictly gated behind `AuthProvider`'s own `isLoading`
 * state) before this initial restoration finishes, sending a request
 * with no Authorization header - which the backend correctly rejects
 * as 401, since it never fabricates a fallback identity. Awaiting the
 * SAME promise `AuthProvider` uses (rather than each side independently
 * calling `getSession()` and hoping they finish in a compatible order)
 * removes that race entirely.
 */
export const sessionReady = supabase.auth.getSession().then(({ data }) => data.session);