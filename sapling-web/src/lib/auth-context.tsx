"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { createClient } from "@/lib/supabase";
import type { User, Session } from "@supabase/supabase-js";
import { startSession, endSession, getSessionId } from "@/lib/use-session-heartbeat";

export interface CompanyProfile {
  label?: string;
  company_name?: string;
  reg_number?: string;
  vat_number?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
}

export interface Profile {
  id: string;
  name: string;
  role: string;
  email: string;
  phone: string | null;
  company: string | null;
  company_details?: CompanyProfile[] | CompanyProfile | null;
}

/** Normalise company_details to always be an array. */
export function getCompanyProfiles(profile: Profile | null): CompanyProfile[] {
  if (!profile?.company_details) return [];
  if (Array.isArray(profile.company_details)) return profile.company_details;
  // Single object → wrap in array
  return [profile.company_details];
}

interface AuthContextValue {
  user: User | null;
  profile: Profile | null;
  isAdmin: boolean;
  isLoading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  profile: null,
  isAdmin: false,
  isLoading: true,
  signOut: async () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

async function fetchProfile(userId: string): Promise<Profile | null> {
  const supabase = createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select("*")
    .eq("id", userId)
    .single();

  if (error) {
    console.error("Failed to fetch profile:", error.message);
    return null;
  }
  return data as Profile;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const sessionStartedRef = useRef(false);

  const loadProfile = useCallback(async (session: Session | null) => {
    if (!session?.user) {
      setUser(null);
      setProfile(null);
      setIsLoading(false);
      return;
    }
    setUser(session.user);
    const p = await fetchProfile(session.user.id);
    setProfile(p);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    const supabase = createClient();

    // Check current session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      loadProfile(session);
      // Start session tracking if authenticated and not already started
      if (session?.user && !getSessionId() && !sessionStartedRef.current) {
        sessionStartedRef.current = true;
        startSession().catch(() => {});
      }
    });

    // Subscribe to auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      loadProfile(session);
      // Start a new session on explicit sign-in
      if (event === "SIGNED_IN" && session?.user && !getSessionId()) {
        startSession().catch(() => {});
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [loadProfile]);

  const signOut = useCallback(async () => {
    // End the tracking session before signing out
    await endSession();
    sessionStartedRef.current = false;
    const supabase = createClient();
    await supabase.auth.signOut();
    setUser(null);
    setProfile(null);
  }, []);

  const isAdmin = profile?.role === "admin";

  return (
    <AuthContext value={{ user, profile, isAdmin, isLoading, signOut }}>
      {children}
    </AuthContext>
  );
}
