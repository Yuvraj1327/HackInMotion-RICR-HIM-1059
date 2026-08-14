import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
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
  // Tracks whose data the cache currently holds, so the listener below
  // can tell "still the same session" apart from "a different account
  // just took over this tab" (including a DIFFERENT session replacing
  // this one without ever calling logout() first - e.g. another browser
  // tab signing in as someone else, which Supabase's client broadcasts
  // to every tab sharing the same localStorage).
  const currentUserIdRef = useRef<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      currentUserIdRef.current = data.session?.user.id ?? null;
      setSession(data.session);
      setIsGuest(!!data.session && readGuestFlag());
      setIsLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      const newUserId = newSession?.user.id ?? null;

      // This is the SINGLE authoritative place every session transition
      // passes through - whether it came from login()/signup()/
      // continueAsGuest()/logout() in this tab, a background token
      // refresh, or another tab signing in/out as a different account.
      // Whenever the authenticated user actually changes (including to
      // or from "nobody"), wipe every cached query result so a
      // Dashboard/Inventory/etc. that's already mounted can never keep
      // showing the PREVIOUS account's numbers under the new session -
      // this is what actually prevents guest <-> real-account data
      // leakage, rather than relying only on the explicit clears inside
      // the four auth functions below (which don't cover paths that
      // bypass them, like cross-tab sync).
      if (newUserId !== currentUserIdRef.current) {
        queryClient.clear();
        setIsGuest(!!newSession && readGuestFlag());
        if (!newSession) writeGuestFlag(false);
      }

      currentUserIdRef.current = newUserId;
      setSession(newSession);
    });

    return () => listener.subscription.unsubscribe();
  }, [queryClient]);

  /**
   * Shared by `signup` and `continueAsGuest`: registers via the backend
   * (creating both the Supabase Auth user and the `profiles` row) and
   * hydrates the Supabase JS client's own session store with the
   * returned tokens.
   *
   * Returns the session directly and applies it to React state
   * synchronously here, rather than waiting for `onAuthStateChange` to
   * pick it up. Supabase's listener dispatches via a deferred
   * `setTimeout(0)` (to avoid re-entrancy), so relying on it alone is a
   * real race: a plain `signInWithPassword` call involves a network
   * round-trip long enough for that timeout to fire first, but
   * `setSession()` with tokens already in hand is a purely local
   * operation that can resolve BEFORE the listener runs. Any caller
   * that navigates immediately after (e.g. straight to /dashboard)
   * could hit `ProtectedRoute` while `session` state is still stale and
   * get bounced back to /login before the listener ever catches up.
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

    const { data, error } = await supabase.auth.setSession({
      access_token: result.access_token,
      refresh_token: result.refresh_token ?? "",
    });
    if (error) throw new ApiError(error.message, null, "session_error");

    currentUserIdRef.current = data.session?.user.id ?? null;
    setSession(data.session);
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
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      throw new ApiError(
        error.message === "Invalid login credentials"
          ? "Incorrect email or password."
          : error.message,
        401,
        "invalid_credentials"
      );
    }
    // Applied synchronously - see registerAndEstablishSession's comment
    // on why this can't wait for onAuthStateChange alone.
    currentUserIdRef.current = data.session?.user.id ?? null;
    setSession(data.session);
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

    const { data, error } = await supabase.auth.setSession({
      access_token: result.access_token,
      refresh_token: result.refresh_token ?? "",
    });
    if (error) throw new ApiError(error.message, null, "session_error");

    // Applied synchronously and BEFORE returning - this is the fix for
    // "guest dashboard doesn't show": setSession() here is a purely
    // local operation (the tokens are already in hand, no network
    // round-trip), so it can resolve before onAuthStateChange's
    // deferred listener fires. Without this, the caller's immediate
    // navigate("/dashboard") could run while `session` React state is
    // still null, and ProtectedRoute would redirect straight back to
    // /login before the listener ever catches up.
    currentUserIdRef.current = data.session?.user.id ?? null;
    setSession(data.session);

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