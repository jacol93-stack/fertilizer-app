"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { History, X } from "lucide-react";

interface Session {
  id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  ip_address: string | null;
  device_type: string;
  browser: string;
  os: string;
}

interface SessionLogData {
  user_id: string;
  user_name: string;
  sessions: Session[];
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "Active";
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-ZA", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function SessionLogPanel({
  selectedUserId,
  selectedUserName,
  onClose,
}: {
  selectedUserId: string | null;
  selectedUserName?: string;
  onClose: () => void;
}) {
  const [data, setData] = useState<SessionLogData | null>(null);
  const [loading, setLoading] = useState(false);

  const loadSessions = useCallback(async (userId: string) => {
    setLoading(true);
    try {
      const result = await api.get<SessionLogData>(
        `/api/admin/dashboard/user-sessions?user_id=${userId}&days=30`
      );
      setData(result);
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (selectedUserId) {
      loadSessions(selectedUserId);
    } else {
      setData(null);
    }
  }, [selectedUserId, loadSessions]);

  if (!selectedUserId) return null;

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="size-4 text-[#00d4ff]" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
            Sessions — {data?.user_name || selectedUserName || "User"}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-[#6b7280] hover:bg-[#1e1e2e] hover:text-[#e5e7eb]"
        >
          <X className="size-4" />
        </button>
      </div>

      {loading ? (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-8 text-center text-sm text-[#4a4a5a]">
          Loading sessions...
        </div>
      ) : !data?.sessions.length ? (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-8 text-center text-sm text-[#4a4a5a]">
          No sessions found for this user in the last 30 days
        </div>
      ) : (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#1e1e2e] text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3 text-right">Duration</th>
                <th className="hidden px-4 py-3 sm:table-cell">IP</th>
                <th className="hidden px-4 py-3 md:table-cell">Device</th>
                <th className="hidden px-4 py-3 md:table-cell">Browser</th>
                <th className="hidden px-4 py-3 lg:table-cell">OS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e2e]">
              {data.sessions.map((s) => (
                <tr key={s.id} className="text-[#c9c9d0] hover:bg-[#1a1a24]">
                  <td className="px-4 py-2.5 text-xs">
                    {formatTime(s.started_at)}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">
                    <span
                      className={
                        s.ended_at
                          ? "text-[#6b7280]"
                          : "font-medium text-[#00ff88]"
                      }
                    >
                      {formatDuration(s.duration_seconds)}
                    </span>
                  </td>
                  <td className="hidden px-4 py-2.5 font-mono text-xs text-[#6b7280] sm:table-cell">
                    {s.ip_address || "--"}
                  </td>
                  <td className="hidden px-4 py-2.5 text-xs capitalize text-[#6b7280] md:table-cell">
                    {s.device_type}
                  </td>
                  <td className="hidden px-4 py-2.5 text-xs text-[#6b7280] md:table-cell">
                    {s.browser}
                  </td>
                  <td className="hidden px-4 py-2.5 text-xs text-[#6b7280] lg:table-cell">
                    {s.os}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
