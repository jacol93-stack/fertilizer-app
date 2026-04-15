"use client";

import { MetricCard } from "./metric-card";
import { SparklineChart } from "./sparkline-chart";
import { Users } from "lucide-react";

interface UserAnalyticsData {
  period_days: number;
  total_users: number;
  active_users: number;
  total_sessions: number;
  avg_session_minutes: number;
  users: Array<{
    user_id: string;
    name: string;
    email: string;
    role: string;
    company: string;
    last_login_at: string | null;
    session_count: number;
    total_minutes: number;
    avg_session_minutes: number;
    primary_device: string;
    primary_browser: string;
  }>;
  device_breakdown: Array<{ device_type: string; count: number }>;
  daily_active_users: Array<{ date: string; count: number }>;
}

function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffH = diffMs / 3600000;

  if (diffH < 1) return `${Math.round(diffMs / 60000)}m ago`;
  if (diffH < 24) return `${Math.round(diffH)}h ago`;
  const diffD = Math.round(diffH / 24);
  if (diffD === 1) return "Yesterday";
  if (diffD < 7) return `${diffD}d ago`;
  return d.toLocaleDateString("en-ZA", { day: "numeric", month: "short" });
}

function DeviceBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    desktop: "#00ff88",
    mobile: "#00d4ff",
    tablet: "#ff4f00",
  };
  const color = colors[type] || "#6b7280";
  return (
    <span
      className="inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
      style={{ color, border: `1px solid ${color}30`, backgroundColor: `${color}10` }}
    >
      {type}
    </span>
  );
}

export function UserAnalyticsPanel({
  data,
  onSelectUser,
}: {
  data: UserAnalyticsData | null;
  onSelectUser?: (userId: string) => void;
}) {
  if (!data) {
    return (
      <section>
        <div className="mb-4 flex items-center gap-2">
          <Users className="size-4 text-[#ff4f00]" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
            User Analytics
          </h2>
        </div>
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-8 text-center text-sm text-[#4a4a5a]">
          Loading...
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <Users className="size-4 text-[#ff4f00]" />
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
          User Analytics
          <span className="ml-2 text-[#4a4a5a]">({data.period_days}d)</span>
        </h2>
      </div>

      {/* Summary cards */}
      <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard label="Total Users" value={data.total_users} color="white" />
        <MetricCard label="Active Users" value={data.active_users} color="green" />
        <MetricCard label="Total Sessions" value={data.total_sessions} color="cyan" />
        <MetricCard
          label="Avg Session"
          value={`${data.avg_session_minutes}m`}
          color="orange"
        />
      </div>

      {/* DAU chart + device breakdown */}
      <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* DAU Chart */}
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4 md:col-span-2">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
            Daily Active Users
          </p>
          <SparklineChart
            data={data.daily_active_users}
            dataKey="count"
            color="#00ff88"
            height={120}
            showGrid
            formatValue={(v) => `${v} users`}
          />
        </div>

        {/* Device breakdown */}
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
            Devices
          </p>
          <div className="space-y-3">
            {data.device_breakdown.map((d) => {
              const total = data.device_breakdown.reduce((s, x) => s + x.count, 0);
              const pct = total ? Math.round((d.count / total) * 100) : 0;
              const colors: Record<string, string> = {
                desktop: "#00ff88",
                mobile: "#00d4ff",
                tablet: "#ff4f00",
              };
              const color = colors[d.device_type] || "#6b7280";

              return (
                <div key={d.device_type}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="capitalize text-[#c9c9d0]">{d.device_type}</span>
                    <span className="tabular-nums" style={{ color }}>
                      {d.count} ({pct}%)
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-[#1e1e2e]">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* User leaderboard table */}
      {data.users.length > 0 && (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#1e1e2e] text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
                <th className="px-4 py-3">User</th>
                <th className="hidden px-4 py-3 sm:table-cell">Company</th>
                <th className="px-4 py-3 text-right">Sessions</th>
                <th className="hidden px-4 py-3 text-right sm:table-cell">Time</th>
                <th className="px-4 py-3 text-right">Last Login</th>
                <th className="hidden px-4 py-3 text-center md:table-cell">Device</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e2e]">
              {data.users.map((u) => (
                <tr
                  key={u.user_id}
                  className="cursor-pointer text-[#c9c9d0] hover:bg-[#1a1a24]"
                  onClick={() => onSelectUser?.(u.user_id)}
                >
                  <td className="px-4 py-2.5">
                    <div className="font-medium text-[#e5e7eb]">{u.name}</div>
                    <div className="text-[11px] text-[#6b7280]">{u.email}</div>
                  </td>
                  <td className="hidden px-4 py-2.5 text-[#6b7280] sm:table-cell">
                    {u.company || "--"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-[#00d4ff]">
                    {u.session_count}
                  </td>
                  <td className="hidden px-4 py-2.5 text-right tabular-nums text-[#6b7280] sm:table-cell">
                    {u.total_minutes < 60
                      ? `${u.total_minutes}m`
                      : `${(u.total_minutes / 60).toFixed(1)}h`}
                  </td>
                  <td className="px-4 py-2.5 text-right text-xs text-[#6b7280]">
                    {formatDate(u.last_login_at)}
                  </td>
                  <td className="hidden px-4 py-2.5 text-center md:table-cell">
                    <DeviceBadge type={u.primary_device} />
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
