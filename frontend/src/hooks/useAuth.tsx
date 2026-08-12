import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { registerAccount, guestLogin } from "@/api/auth";
import { seedDemoData } from "@/api/demo";
import { listProducts } from "@/api/products";
import { ApiError } from "@/api/client";
import { GUEST_DEMO_SEED, GUEST_MODE_STORAGE_KEY } from "@/lib/constants";

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  businessEmail: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isGuest: boolean;
  signup: (email: string, password: string, businessName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /**
   * "Continue as Guest" for hackathon/demo testing. This is NOT a
   * separate auth system: it calls the backend's dedicated `/auth/guest`
   * endpoint, which reuses a single well-known guest account (see the
   * backend's docstring - it does not provision a new Supabase user on
   * every click) via the admin API (not the public sign-up flow), and
   * returns a genuine Supabase-issued session. If that guest account
   * has no data yet, it's seeded once via the existing `/demo/seed`
   * endpoint - repeat guest sessions reuse the same seeded data rather
   * than piling up duplicates. The resulting session is a completely
   * ordinary authenticated session - every subsequent request still
   * carries a real bearer token and is still subject to the backend's
   * user-id filtering and Supabase RLS, exactly like any other
   * account. `isGuest` only controls the DEMO MODE badge; it grants no
   * extra access.
   */
  continueAsGuest: () => Promise<{ seeded: boolean }>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readGuestFlag(): boolean {
  try {
    return localStorage.getItem(GUEST_MODE_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function writeGuestFlag(value: boolean) {
  try {
    if (value) localStorage.setItem(GUEST_MODE_STORAGE_KEY, "true");
    else localStorage.removeItem(GUEST_MODE_STORAGE_KEY);
  } catch {
    // localStorage unavailable (e.g. private browsing) - badge simply won't
    // persist across reloads, which is a harmless cosmetic degradation.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGuest, setIsGuest] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setIsGuest(!!data.session && readGuestFlag());
      setIsLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      if (!newSession) {
        // Session ended (e.g. sign-out from another tab) - clear the flag too.
        writeGuestFlag(false);
        setIsGuest(false);
      }
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  /**
   * Shared by `signup` and `continueAsGuest`: registers via the backend
   * (creating both the Supabase Auth user and the `profiles` row) and
   * hydrates the Supabase JS client's own session store with the
   * returned tokens so autoRefreshToken takes over from here exactly as
   * it would for a client-side signup.
   */
  async function registerAndEstablishSession(email: string, password: string, businessName: string) {
    const result = await registerAccount({ email, password, business_name: businessName });

    if (!result.access_token) {
      // Supabase project has "confirm email" enabled - no session yet.
      throw new ApiError(
        "Account created. Please check your email to confirm your address, then log in.",
        null,
        "email_confirmation_required"
      );
    }

    const { error } = await supabase.auth.setSession({
      access_token: result.access_token,
      refresh_token: result.refresh_token ?? "",
    });
    if (error) throw new ApiError(error.message, null, "session_error");
  }

  async function signup(email: string, password: string, businessName: string) {
    await registerAndEstablishSession(email, password, businessName);
    writeGuestFlag(false);
    setIsGuest(false);
    // No user was authenticated before this call could have left stale
    // cached data, but clearing here too keeps the invariant simple:
    // every successful auth transition starts with an empty cache.
    queryClient.clear();
  }

  async function login(email: string, password: string) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      throw new ApiError(
        error.message === "Invalid login credentials"
          ? "Incorrect email or password."
          : error.message,
        401,
        "invalid_credentials"
      );
    }
    writeGuestFlag(false);
    setIsGuest(false);
    // Clear any cached data from a previous session in this tab (e.g. a
    // prior guest or a different account) so Dashboard/Inventory/etc.
    // never show a stale flash of someone else's data before refetching.
    queryClient.clear();
  }

  async function continueAsGuest() {
    // Calls the dedicated backend guest endpoint. It reuses a single
    // shared guest account rather than creating a new Supabase user on
    // every click (see api/auth.ts / backend docstring). Nothing here
    // is hardcoded demo data: only the account identity is handled
    // backend-side; every product, supplier, and sale the guest sees
    // comes from the backend's own /demo/seed endpoint, same as the
    // "Generate Demo Store" flow any normal user can trigger from the
    // Dashboard.
    const result = await guestLogin();

    if (!result.access_token) {
      throw new ApiError("Could not start Demo Mode. Please try again.", null, "session_error");
    }

    const { error } = await supabase.auth.setSession({
      access_token: result.access_token,
      refresh_token: result.refresh_token ?? "",
    });
    if (error) throw new ApiError(error.message, null, "session_error");

    writeGuestFlag(true);
    setIsGuest(true);
    // Same reasoning as login(): guarantee no stale cached data from a
    // previous session (real or guest) leaks into this guest session's
    // Dashboard/Inventory/Forecasts/etc.
    queryClient.clear();

    try {
      // The guest account is shared/reused across sessions, so only
      // seed demo data the first time it's ever used - otherwise every
      // click would keep appending another full demo dataset on top of
      // the last one.
      const existingProducts = await listProducts({ limit: 1 });
      if (existingProducts.length > 0) {
        return { seeded: true };
      }
      await seedDemoData(GUEST_DEMO_SEED);
      return { seeded: true };
    } catch {
      // If checking/seeding fails (e.g. a transient network issue), the
      // guest still lands on a real, authenticated Dashboard - it just
      // starts empty, and the existing "Generate Demo Store" action
      // there covers them. We surface this so the UI can inform them.
      return { seeded: false };
    }
  }

  async function logout() {
    await supabase.auth.signOut();
    writeGuestFlag(false);
    setIsGuest(false);
    // Evict every cached query result so the next login/guest session
    // (in this same tab) never sees this account's data, even for an
    // instant before its own queries resolve.
    queryClient.clear();
  }

  const value: AuthContextValue = {
    session,
    user: session?.user ?? null,
    businessEmail: session?.user?.email ?? null,
    isLoading,
    isAuthenticated: !!session,
    isGuest,
    signup,
    login,
    logout,
    continueAsGuest,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}