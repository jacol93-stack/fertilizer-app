"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { createClient } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Redirect if already logged in
  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/");
    }
  }, [isLoading, user, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const supabase = createClient();
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        setError(authError.message);
        return;
      }

      // Clear session storage from previous user
      sessionStorage.clear();

      router.replace("/");
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  // Don't show login form if already authenticated
  if (!isLoading && user) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#191919] via-[#2a2a2a] to-[#191919] px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-6">
          {/* Logo */}
          <Image
            src="/logo_icon_only.png"
            alt="Sapling"
            width={72}
            height={72}
            priority
          />

          {/* Title */}
          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Sapling
            </h1>
            <p className="mt-1 text-sm text-gray-400">
              Fertilise Smarter, Grow Stronger
            </p>
          </div>

          {/* Login form */}
          <form
            onSubmit={handleSubmit}
            className="w-full space-y-4 rounded-xl bg-white/5 p-6 backdrop-blur-sm"
          >
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="border-white/10 bg-white/5 text-white placeholder:text-gray-500 focus:border-[var(--sapling-orange)]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="border-white/10 bg-white/5 text-white placeholder:text-gray-500 focus:border-[var(--sapling-orange)]"
              />
            </div>

            {error && (
              <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">
                {error}
              </p>
            )}

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-[var(--sapling-orange)] text-white hover:bg-[#e64600]"
            >
              {submitting ? "Signing in..." : "Sign in"}
            </Button>

            <button
              type="button"
              onClick={async () => {
                if (!email) {
                  setError("Enter your email address first");
                  return;
                }
                setSubmitting(true);
                setError(null);
                try {
                  const supabase = createClient();
                  const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
                    redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
                  });
                  if (resetError) {
                    setError(resetError.message);
                  } else {
                    setError(null);
                    alert("Password reset link sent! Check your email.");
                  }
                } catch {
                  setError("Failed to send reset email");
                } finally {
                  setSubmitting(false);
                }
              }}
              className="w-full text-center text-sm text-gray-400 hover:text-[var(--sapling-orange)]"
            >
              Forgot password?
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
