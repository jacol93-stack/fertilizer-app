"use client";

import { GaugeRing } from "./gauge-ring";
import { SparklineChart } from "./sparkline-chart";
import { MetricCard } from "./metric-card";
import { Server } from "lucide-react";

interface VpsData {
  current: {
    cpu_percent?: number;
    memory_percent?: number;
    memory_used_mb?: number;
    memory_total_mb?: number;
    disk_percent?: number;
    disk_used_gb?: number;
    disk_total_gb?: number;
    uptime_seconds?: number;
    uptime_human?: string;
    net_bytes_sent?: number;
    net_bytes_recv?: number;
  };
  history: Array<{
    recorded_at: string;
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  }>;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  return `${(bytes / 1e3).toFixed(0)} KB`;
}

export function VpsMetricsPanel({ data }: { data: VpsData | null }) {
  const c = data?.current;
  const noData = !c || Object.keys(c).length === 0;

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <Server className="size-4 text-[#00ff88]" />
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
          VPS Health
        </h2>
      </div>

      {noData ? (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-8 text-center text-sm text-[#4a4a5a]">
          VPS metrics unavailable — host filesystem not mounted (dev mode)
        </div>
      ) : (
        <div className="space-y-4">
          {/* Gauges row */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="flex items-center justify-center rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
              <GaugeRing
                value={c.cpu_percent ?? 0}
                label="CPU"
              />
            </div>
            <div className="flex items-center justify-center rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
              <GaugeRing
                value={c.memory_percent ?? 0}
                label="Memory"
                subtitle={c.memory_used_mb && c.memory_total_mb
                  ? `${c.memory_used_mb} / ${c.memory_total_mb} MB`
                  : undefined}
              />
            </div>
            <div className="flex items-center justify-center rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
              <GaugeRing
                value={c.disk_percent ?? 0}
                label="Disk"
                subtitle={c.disk_used_gb && c.disk_total_gb
                  ? `${c.disk_used_gb} / ${c.disk_total_gb} GB`
                  : undefined}
              />
            </div>
            <MetricCard
              label="Uptime"
              value={c.uptime_human ?? "--"}
              color="cyan"
              subtitle={c.net_bytes_sent != null && c.net_bytes_recv != null
                ? `Net: ${formatBytes(c.net_bytes_sent)} sent / ${formatBytes(c.net_bytes_recv)} recv`
                : undefined}
            />
          </div>

          {/* Sparklines row */}
          {data.history.length > 0 && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
                  CPU — 24h
                </p>
                <SparklineChart
                  data={data.history}
                  dataKey="cpu_percent"
                  color="#00ff88"
                  height={100}
                  showGrid
                  formatValue={(v) => `${v}%`}
                />
              </div>
              <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-4">
                <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
                  Memory — 24h
                </p>
                <SparklineChart
                  data={data.history}
                  dataKey="memory_percent"
                  color="#00d4ff"
                  height={100}
                  showGrid
                  formatValue={(v) => `${v}%`}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
