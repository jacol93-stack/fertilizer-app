"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Loader2,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

interface VpsMetrics {
  current?: {
    cpu_percent?: number;
    memory_percent?: number;
    disk_percent?: number;
    uptime_human?: string;
  };
}

interface SupabaseMetrics {
  database?: { size_mb?: number; connection_count?: number };
  tables?: Array<{ table_name: string; size_mb: number; row_count?: number }>;
}

interface UserAnalytics {
  total_users?: number;
  active_7d?: number;
  active_30d?: number;
  daily_active?: Array<{ date: string; count: number }>;
}

interface AiUsageSummary {
  total_cost_usd_30d?: number;
  total_calls_30d?: number;
}

interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  user_id: string | null;
  user_email?: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

interface DeletedSummary {
  total?: number;
}

export default function AdminOverviewPage() {
  const [vps, setVps] = useState<VpsMetrics | null>(null);
  const [db, setDb] = useState<SupabaseMetrics | null>(null);
  const [users, setUsers] = useState<UserAnalytics | null>(null);
  const [ai, setAi] = useState<AiUsageSummary | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [deleted, setDeleted] = useState<DeletedSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [vpsRes, dbRes, userRes, aiRes, auditRes, delRes] = await Promise.all([
          api.get<VpsMetrics>(`/api/dashboard/vps-metrics`).catch(() => null),
          api.get<SupabaseMetrics>(`/api/dashboard/supabase-metrics`).catch(() => null),
          api.get<UserAnalytics>(`/api/dashboard/user-analytics?days=30`).catch(() => null),
          api.get<AiUsageSummary>(`/api/admin/ai-usage?days=30`).catch(() => null),
          api
            .get<{ items?: AuditEvent[] } | AuditEvent[]>(`/api/admin/audit-log?limit=10`)
            .catch(() => [] as AuditEvent[]),
          api.get<DeletedSummary>(`/api/admin/deleted?limit=1`).catch(() => null),
        ]);
        setVps(vpsRes);
        setDb(dbRes);
        setUsers(userRes);
        setAi(aiRes);
        const auditList = Array.isArray(auditRes) ? auditRes : auditRes?.items ?? [];
        setAudit(auditList);
        setDeleted(delRes);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Overview</h1>
        <p className="text-sm text-muted-foreground">
          System health, usage, and recent activity at a glance.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tile
          icon={<Cpu className="size-4 text-[var(--sapling-orange)]" />}
          label="VPS"
          value={vps?.current?.cpu_percent != null ? `${vps.current.cpu_percent}% cpu` : "—"}
          sub={
            vps?.current
              ? `${vps.current.memory_percent ?? 0}% mem · ${vps.current.disk_percent ?? 0}% disk`
              : undefined
          }
        />
        <Tile
          icon={<Database className="size-4 text-[var(--sapling-orange)]" />}
          label="Database"
          value={db?.database?.size_mb != null ? `${db.database.size_mb} MB` : "—"}
          sub={
            db?.database?.connection_count != null
              ? `${db.database.connection_count} conns`
              : undefined
          }
        />
        <Tile
          icon={<Users className="size-4 text-[var(--sapling-orange)]" />}
          label="Users"
          value={users?.total_users != null ? `${users.total_users}` : "—"}
          sub={users?.active_7d != null ? `${users.active_7d} active 7d` : undefined}
        />
        <Tile
          icon={<Sparkles className="size-4 text-[var(--sapling-orange)]" />}
          label="AI cost (30d)"
          value={ai?.total_cost_usd_30d != null ? `$${ai.total_cost_usd_30d.toFixed(2)}` : "—"}
          sub={ai?.total_calls_30d != null ? `${ai.total_calls_30d} calls` : undefined}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--sapling-dark)]">Recent activity</h2>
              <Link href="/admin/audit" className="text-xs text-muted-foreground hover:text-[var(--sapling-orange)]">
                View all →
              </Link>
            </div>
            {audit.length === 0 ? (
              <p className="py-4 text-center text-xs text-muted-foreground">
                No audit events recorded.
              </p>
            ) : (
              <ul className="space-y-1">
                {audit.slice(0, 8).map((e) => (
                  <li key={e.id} className="flex items-center justify-between gap-2 text-xs">
                    <span className="flex min-w-0 items-center gap-2">
                      <Activity className="size-3 shrink-0 text-muted-foreground" />
                      <span className="truncate">
                        <span className="font-medium text-[var(--sapling-dark)]">
                          {e.user_email ?? "—"}
                        </span>{" "}
                        <span className="text-muted-foreground">
                          {e.event_type}
                          {e.entity_type ? ` · ${e.entity_type}` : ""}
                        </span>
                      </span>
                    </span>
                    <span className="shrink-0 text-[10px] text-muted-foreground tabular-nums">
                      {new Date(e.created_at).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--sapling-dark)]">Top tables</h2>
              <span className="text-xs text-muted-foreground">by size</span>
            </div>
            {!db?.tables || db.tables.length === 0 ? (
              <p className="py-4 text-center text-xs text-muted-foreground">
                Database metrics unavailable.
              </p>
            ) : (
              <ul className="space-y-1">
                {db.tables.slice(0, 8).map((t) => (
                  <li key={t.table_name} className="flex items-center justify-between gap-2 text-xs">
                    <span className="flex min-w-0 items-center gap-2">
                      <HardDrive className="size-3 shrink-0 text-muted-foreground" />
                      <span className="truncate font-mono text-[11px]">{t.table_name}</span>
                    </span>
                    <span className="shrink-0 tabular-nums text-muted-foreground">
                      {t.size_mb} MB
                      {t.row_count != null ? ` · ${t.row_count.toLocaleString()} rows` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {(deleted?.total ?? 0) > 0 && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardContent className="flex items-center justify-between gap-3 py-3">
            <div className="flex items-center gap-2 text-sm text-amber-900">
              <Trash2 className="size-4" />
              <span>
                {deleted!.total} soft-deleted {deleted!.total === 1 ? "record" : "records"} awaiting
                review
              </span>
            </div>
            <Link
              href="/admin/trash"
              className="rounded-md border border-amber-300 bg-white px-3 py-1 text-xs font-medium text-amber-900 hover:bg-amber-100"
            >
              Open recovery →
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Tile({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {icon}
          {label}
        </div>
        <div className="mt-1.5 text-xl font-semibold text-[var(--sapling-dark)] tabular-nums">
          {value}
        </div>
        {sub && (
          <div className="mt-0.5 text-[11px] text-muted-foreground">{sub}</div>
        )}
      </CardContent>
    </Card>
  );
}
