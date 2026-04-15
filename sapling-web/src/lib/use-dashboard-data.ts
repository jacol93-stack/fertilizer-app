"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";

const POLL_INTERVAL_MS = 30_000; // 30 seconds

interface VpsMetrics {
  current: Record<string, unknown>;
  history: Array<Record<string, unknown>>;
}

interface SupabaseMetrics {
  database: { size_bytes: number; size_mb: number; connection_count: number };
  tables: Array<{
    table_name: string;
    row_estimate: number;
    size_bytes: number;
    size_mb: number;
  }>;
}

interface UserAnalytics {
  period_days: number;
  total_users: number;
  active_users: number;
  total_sessions: number;
  avg_session_minutes: number;
  users: Array<Record<string, unknown>>;
  device_breakdown: Array<{ device_type: string; count: number }>;
  daily_active_users: Array<{ date: string; count: number }>;
}

export interface DashboardData {
  vps: VpsMetrics | null;
  supabase: SupabaseMetrics | null;
  analytics: UserAnalytics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useDashboardData(): DashboardData {
  const [vps, setVps] = useState<VpsMetrics | null>(null);
  const [supabase, setSupabase] = useState<SupabaseMetrics | null>(null);
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setError(null);
      const [vpsRes, sbRes, analyticsRes] = await Promise.allSettled([
        api.get<VpsMetrics>("/api/admin/dashboard/vps-metrics"),
        api.get<SupabaseMetrics>("/api/admin/dashboard/supabase-metrics"),
        api.get<UserAnalytics>("/api/admin/dashboard/user-analytics?days=30"),
      ]);

      if (vpsRes.status === "fulfilled") setVps(vpsRes.value);
      if (sbRes.status === "fulfilled") setSupabase(sbRes.value);
      if (analyticsRes.status === "fulfilled") setAnalytics(analyticsRes.value);

      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();

    intervalRef.current = setInterval(fetchAll, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchAll]);

  return { vps, supabase, analytics, loading, error, lastUpdated, refresh: fetchAll };
}
