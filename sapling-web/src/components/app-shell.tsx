"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Nav } from "@/components/nav";
import { ImpersonationBanner } from "@/components/impersonation-banner";
import { useSessionHeartbeat } from "@/lib/use-session-heartbeat";
import type { ReactNode } from "react";

function LoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-[var(--sapling-orange)]" />
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  useSessionHeartbeat();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-[var(--sapling-light-bg)]">
      <ImpersonationBanner />
      <Nav />
      <main className="flex-1">{children}</main>
    </div>
  );
}
