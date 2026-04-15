"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useDashboardData } from "@/lib/use-dashboard-data";
import { AppShell } from "@/components/app-shell";
import { VpsMetricsPanel } from "@/components/dashboard/vps-metrics-panel";
import { SupabaseMetricsPanel } from "@/components/dashboard/supabase-metrics-panel";
import { UserAnalyticsPanel } from "@/components/dashboard/user-analytics-panel";
import { SessionLogPanel } from "@/components/dashboard/session-log-panel";
import { RefreshCw, Activity } from "lucide-react";

function secondsAgo(date: Date | null): string {
  if (!date) return "--";
  const s = Math.round((Date.now() - date.getTime()) / 1000);
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;
  return `${Math.round(s / 60)}m ago`;
}

export default function AdminDashboardPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { vps, supabase, analytics, loading, error, lastUpdated, refresh } =
    useDashboardData();

  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [timeLabel, setTimeLabel] = useState("--");

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace("/");
    }
  }, [authLoading, isAdmin, router]);

  // Update "last updated" label every 5 seconds
  useEffect(() => {
    setTimeLabel(secondsAgo(lastUpdated));
    const id = setInterval(() => setTimeLabel(secondsAgo(lastUpdated)), 5000);
    return () => clearInterval(id);
  }, [lastUpdated]);

  if (authLoading) return null;

  return (
    <AppShell>
      <div
        className="min-h-screen px-4 py-6 sm:px-6 lg:px-8"
        style={{ backgroundColor: "#0a0a0f", color: "#e5e7eb" }}
      >
        <div className="mx-auto max-w-7xl">
          {/* Header */}
          <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-[#12121a] border border-[#1e1e2e]">
                <Activity className="size-5 text-[#00ff88]" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#e5e7eb]">Dashboard</h1>
                <p className="text-xs text-[#6b7280]">
                  System telemetry & user analytics
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs tabular-nums text-[#4a4a5a]">
                Updated {timeLabel}
              </span>
              <button
                onClick={refresh}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg border border-[#1e1e2e] bg-[#12121a] px-3 py-1.5 text-xs font-medium text-[#6b7280] transition-colors hover:border-[#00ff88] hover:text-[#00ff88] disabled:opacity-50"
              >
                <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>
          </div>

          {/* Error banner */}
          {error && (
            <div className="mb-6 rounded-xl border border-[#ff335530] bg-[#ff335510] p-4 text-sm text-[#ff3355]">
              {error}
            </div>
          )}

          {/* Loading state */}
          {loading && !vps && !supabase && !analytics ? (
            <div className="flex min-h-[400px] items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="size-8 animate-spin rounded-full border-2 border-[#1e1e2e] border-t-[#00ff88]" />
                <p className="text-sm text-[#6b7280]">Loading dashboard...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {/* VPS Health */}
              <VpsMetricsPanel data={vps as Parameters<typeof VpsMetricsPanel>[0]["data"]} />

              {/* Supabase */}
              <SupabaseMetricsPanel data={supabase as Parameters<typeof SupabaseMetricsPanel>[0]["data"]} />

              {/* User Analytics */}
              <UserAnalyticsPanel
                data={analytics as Parameters<typeof UserAnalyticsPanel>[0]["data"]}
                onSelectUser={(userId) => setSelectedUserId(userId)}
              />

              {/* Session Log (appears when a user is selected) */}
              <SessionLogPanel
                selectedUserId={selectedUserId}
                onClose={() => setSelectedUserId(null)}
              />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
