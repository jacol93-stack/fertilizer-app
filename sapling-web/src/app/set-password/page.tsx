"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { createClient } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

export default function SetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [ready, setReady] = useState(false);
  const router = useRouter();

  // Session should already exist (set by /auth/callback route)
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setReady(true);
      } else {
        setError("Invalid or expired invite link. Please contact your administrator.");
      }
    });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSubmitting(true);
    try {
      const supabase = createClient();
      const { error: updateError } = await supabase.auth.updateUser({
        password,
      });

      if (updateError) {
        setError(updateError.message);
        return;
      }

      setSuccess(true);
      setTimeout(() => router.replace("/"), 2000);
    } catch {
      setError("An unexpected error occurred");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#191919] via-[#2a2a2a] to-[#191919] px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-6">
          <Image
            src="/logo_icon_only.png"
            alt="Sapling"
            width={72}
            height={72}
            priority
          />

          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Welcome to Sapling
            </h1>
            <p className="mt-1 text-sm text-gray-400">
              Create your password to get started
            </p>
          </div>

          {success ? (
            <div className="w-full rounded-xl bg-green-500/10 p-6 text-center">
              <p className="text-sm text-green-400">
                Account activated! Redirecting to the app...
              </p>
            </div>
          ) : !ready && !error ? (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="size-4 animate-spin" />
              <span className="text-sm">Verifying invite link...</span>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="w-full space-y-4 rounded-xl bg-white/5 p-6 backdrop-blur-sm"
            >
              <div className="space-y-2">
                <Label htmlFor="password" className="text-gray-300">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="At least 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  className="border-white/10 bg-white/5 text-white placeholder:text-gray-500 focus:border-[var(--sapling-orange)]"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm" className="text-gray-300">
                  Confirm Password
                </Label>
                <Input
                  id="confirm"
                  type="password"
                  placeholder="Repeat your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
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
                disabled={submitting || !ready}
                className="w-full bg-[var(--sapling-orange)] text-white hover:bg-[#e64600]"
              >
                {submitting ? "Activating..." : "Activate Account"}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
