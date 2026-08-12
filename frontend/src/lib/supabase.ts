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
