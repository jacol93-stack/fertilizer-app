"use client";

import { MetricCard } from "./metric-card";
import { Database } from "lucide-react";

interface SupabaseData {
  database: {
    size_bytes: number;
    size_mb: number;
    connection_count: number;
  };
  tables: Array<{
    table_name: string;
    row_estimate: number;
    size_bytes: number;
    size_mb: number;
  }>;
}

function formatSize(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${mb.toFixed(1)} MB`;
}

export function SupabaseMetricsPanel({ data }: { data: SupabaseData | null }) {
  if (!data) {
    return (
      <section>
        <div className="mb-4 flex items-center gap-2">
          <Database className="size-4 text-[#00d4ff]" />
          <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
            Supabase
          </h2>
        </div>
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-8 text-center text-sm text-[#4a4a5a]">
          Loading...
        </div>
      </section>
    );
  }

  const tables = (data.tables || []).filter(t => t.row_estimate > 0);

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <Database className="size-4 text-[#00d4ff]" />
        <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b7280]">
          Supabase
        </h2>
      </div>

      {/* Summary cards */}
      <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <MetricCard
          label="Database Size"
          value={formatSize(data.database.size_mb)}
          color="cyan"
        />
        <MetricCard
          label="Connections"
          value={data.database.connection_count}
          color="green"
        />
        <MetricCard
          label="Tables"
          value={tables.length}
          color="white"
        />
      </div>

      {/* Table breakdown */}
      {tables.length > 0 && (
        <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#1e1e2e] text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
                <th className="px-4 py-3">Table</th>
                <th className="px-4 py-3 text-right">Rows</th>
                <th className="px-4 py-3 text-right">Size</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e2e]">
              {tables.map((t) => (
                <tr key={t.table_name} className="text-[#c9c9d0] hover:bg-[#1a1a24]">
                  <td className="px-4 py-2.5 font-mono text-xs">{t.table_name}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">
                    {t.row_estimate.toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-[#6b7280]">
                    {t.size_mb < 1 ? `${(t.size_mb * 1024).toFixed(0)} KB` : `${t.size_mb.toFixed(1)} MB`}
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
