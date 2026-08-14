import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { supabase, sessionReady } from "@/lib/supabase";
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
  const currentUserIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Uses the SAME promise api/client.ts's request interceptor awaits
    // (see lib/supabase.ts) rather than calling getSession() again
    // independently - one shared bootstrap, not two racing ones.
    sessionReady.then((initialSession) => {
      currentUserIdRef.current = initialSession?.user.id ?? null;
      setSession(initialSession);
      setIsGuest(!!initialSession && readGuestFlag());
      setIsLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      const newUserId = newSession?.user.id ?? null;

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

  async function registerAndEstablishSession(email: string, password: string, businessName: string) {
    const result = await registerAccount({ email, password, business_name: businessName });

    if (!result.access_token) {
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
    currentUserIdRef.current = data.session?.user.id ?? null;
    setSession(data.session);
    writeGuestFlag(false);
    setIsGuest(false);
    queryClient.clear();
  }

  async function continueAsGuest() {
    const result = await guestLogin();

    if (!result.access_token) {
      throw new ApiError("Could not start Demo Mode. Please try again.", null, "session_error");
    }

    const { data, error } = await supabase.auth.setSession({
      access_token: result.access_token,
      refresh_token: result.refresh_token ?? "",
    });
    if (error) throw new ApiError(error.message, null, "session_error");

    currentUserIdRef.current = data.session?.user.id ?? null;
    setSession(data.session);

    writeGuestFlag(true);
    setIsGuest(true);
    queryClient.clear();

    try {
      const existingProducts = await listProducts({ limit: 1 });
      if (existingProducts.length > 0) {
        return { seeded: true };
      }
      await seedDemoData(GUEST_DEMO_SEED);
      return { seeded: true };
    } catch {
      return { seeded: false };
    }
  }

  async function logout() {
    await supabase.auth.signOut();
    writeGuestFlag(false);
    setIsGuest(false);
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