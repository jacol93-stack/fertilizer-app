"use client";

/**
 * Agent workbench — the dashboard every agent lands on at /.
 *
 * Replaces the previous "recent 5 of each" layout with one that answers
 * the question "what needs my attention today?". Single round-trip to
 * /api/workbench/workbench; the backend handles all aggregation.
 *
 * Layout:
 *   - Welcome header with "you have N things to look at" summary
 *   - Quick-actions row (4 primary CTAs)
 *   - Stats strip (clients / farms / fields / programmes / quotes / MTD)
 *   - Two columns on desktop, stacked on mobile:
 *       left  = attention cards (stale, never-analysed, pending, unread)
 *       right = recent activity feed
 *   - Onboarding state replaces everything for a brand-new agent
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Calendar,
  ChevronRight,
  Clock,
  FileText,
  FlaskConical,
  Inbox,
  Leaf,
  MessageSquare,
  Plus,
  Sparkles,
  TestTube,
  Users,
} from "lucide-react";

// ── Types (mirror the backend workbench response) ────────────────────────

interface WorkbenchStats {
  clients: number;
  farms: number;
  fields: number;
  analyses_this_month: number;
  active_programmes: number;
  pending_quotes: number;
}

interface StaleAnalysis {
  analysis_id: string;
  client_id: string | null;
  customer: string;
  farm: string;
  field: string;
  crop: string;
  last_analysed_at: string;
  days_old: number;
}

interface NeverAnalysedClient {
  client_id: string;
  name: string;
}

interface PendingQuote {
  quote_id: string;
  client_id: string | null;
  customer: string;
  blend_name: string;
  days_pending: number;
}

interface AttentionSection<T> {
  count: number;
  preview: T[];
}

interface ActivityItem {
  type: "blend" | "soil_analysis" | "programme";
  id: string;
  title: string;
  subtitle: string;
  created_at: string;
  href: string;
}

interface WorkbenchResponse {
  user: { id: string; name?: string; email?: string; role: string };
  stats: WorkbenchStats;
  attention: {
    stale_analyses: AttentionSection<StaleAnalysis>;
    clients_never_analysed: AttentionSection<NeverAnalysedClient>;
    pending_quotes: AttentionSection<PendingQuote>;
    unread_messages: number;
  };
  recent_activity: ActivityItem[];
  is_onboarding: boolean;
  thresholds: { stale_analysis_months: number };
}

// ── Small presentational helpers ─────────────────────────────────────────

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex-1 min-w-[7rem] text-center">
      <div className="text-2xl font-bold text-[var(--sapling-dark)] tabular-nums">
        {value}
      </div>
      <div className="mt-0.5 text-xs uppercase tracking-wide text-[var(--sapling-medium-grey)]">
        {label}
      </div>
    </div>
  );
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.floor(hr / 24);
  if (d < 30) return `${d}d ago`;
  const mo = Math.floor(d / 30);
  if (mo < 12) return `${mo}mo ago`;
  return `${Math.floor(mo / 12)}y ago`;
}

type CardTone = "warning" | "alert" | "info" | "neutral";

const TONE_STYLES: Record<CardTone, { border: string; icon: string; badge: string }> = {
  warning: {
    border: "border-amber-200",
    icon: "text-amber-600 bg-amber-50",
    badge: "bg-amber-100 text-amber-800",
  },
  alert: {
    border: "border-red-200",
    icon: "text-red-600 bg-red-50",
    badge: "bg-red-100 text-red-800",
  },
  info: {
    border: "border-blue-200",
    icon: "text-blue-600 bg-blue-50",
    badge: "bg-blue-100 text-blue-800",
  },
  neutral: {
    border: "border-gray-200",
    icon: "text-gray-600 bg-gray-50",
    badge: "bg-gray-100 text-gray-800",
  },
};

function AttentionCard({
  tone,
  icon: Icon,
  title,
  count,
  emptyMessage,
  viewAllHref,
  children,
}: {
  tone: CardTone;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  count: number;
  emptyMessage: string;
  viewAllHref?: string;
  children: React.ReactNode;
}) {
  const styles = TONE_STYLES[tone];
  return (
    <div className={`rounded-xl border bg-white p-5 ${styles.border}`}>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`flex size-9 items-center justify-center rounded-lg ${styles.icon}`}>
            <Icon className="size-5" />
          </div>
          <div>
            <h3 className="font-semibold text-[var(--sapling-dark)]">{title}</h3>
            {count > 0 && (
              <span className={`mt-0.5 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${styles.badge}`}>
                {count} {count === 1 ? "item" : "items"}
              </span>
            )}
          </div>
        </div>
        {count > 0 && viewAllHref && (
          <Link
            href={viewAllHref}
            className="inline-flex items-center gap-0.5 text-xs font-medium text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-orange)]"
          >
            View all <ChevronRight className="size-3" />
          </Link>
        )}
      </div>

      {count === 0 ? (
        <p className="py-2 text-sm text-[var(--sapling-medium-grey)]">{emptyMessage}</p>
      ) : (
        <div className="space-y-2">{children}</div>
      )}
    </div>
  );
}

function ActivityIcon({ type }: { type: ActivityItem["type"] }) {
  const map = {
    blend: FlaskConical,
    soil_analysis: TestTube,
    programme: Calendar,
  };
  const Icon = map[type];
  return <Icon className="size-4 shrink-0 text-[var(--sapling-medium-grey)]" />;
}

// ── Skeleton + error states ──────────────────────────────────────────────

function WorkbenchSkeleton() {
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-6 px-4 py-8">
      <div className="h-8 w-64 rounded bg-gray-200" />
      <div className="grid gap-3 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-xl bg-gray-100" />
        ))}
      </div>
      <div className="h-20 rounded-xl bg-gray-100" />
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="h-64 rounded-xl bg-gray-100 lg:col-span-2" />
        <div className="h-64 rounded-xl bg-gray-100" />
      </div>
    </div>
  );
}

function WorkbenchError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12 text-center">
      <AlertTriangle className="mx-auto size-8 text-amber-500" />
      <h2 className="mt-3 text-lg font-semibold text-[var(--sapling-dark)]">
        Couldn&apos;t load your workbench
      </h2>
      <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
        Something went wrong fetching your dashboard data. Try again in a moment.
      </p>
      <Button onClick={onRetry} variant="outline" className="mt-4">
        Retry
      </Button>
    </div>
  );
}

// ── Onboarding (zero-state) ──────────────────────────────────────────────

function OnboardingWelcome({ name }: { name: string }) {
  const steps = [
    {
      icon: Users,
      title: "Add your first client",
      body: "Create a client record so you can attach farms, fields, analyses, and reports.",
      href: "/clients",
      cta: "Add client",
    },
    {
      icon: Leaf,
      title: "Run a soil analysis",
      body: "Enter lab values or upload a lab PDF to get classification, targets, and a feeding plan.",
      href: "/quick-analysis",
      cta: "New analysis",
    },
    {
      icon: FlaskConical,
      title: "Build a blend",
      body: "Plug NPK targets into the optimizer and get a cost-optimised recipe.",
      href: "/quick-blend",
      cta: "New blend",
    },
  ];
  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50 to-white p-8">
        <div className="flex items-center gap-3">
          <Sparkles className="size-6 text-[var(--sapling-orange)]" />
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
            Welcome to Sapling, {name}
          </h1>
        </div>
        <p className="mt-2 text-[var(--sapling-medium-grey)]">
          Let&apos;s get you set up. Three steps to your first report.
        </p>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {steps.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={s.title} className="rounded-xl border bg-white p-5">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[var(--sapling-orange)]">
                Step {i + 1}
              </div>
              <div className="mb-3 flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
                <Icon className="size-5" />
              </div>
              <h3 className="font-semibold text-[var(--sapling-dark)]">{s.title}</h3>
              <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">{s.body}</p>
              <Link href={s.href} className="mt-4 inline-block">
                <Button
                  variant="outline"
                  className="w-full border-[var(--sapling-orange)]/40 text-[var(--sapling-orange)] hover:bg-orange-50"
                >
                  <Plus className="size-4" />
                  {s.cta}
                </Button>
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main workbench page ──────────────────────────────────────────────────

export default function WorkbenchPage() {
  const { profile, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<WorkbenchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await api.get<WorkbenchResponse>("/api/workbench/workbench");
      setData(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    load();
  }, [authLoading, load]);

  if (loading) {
    return (
      <AppShell>
        <WorkbenchSkeleton />
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <WorkbenchError onRetry={load} />
      </AppShell>
    );
  }

  if (data.is_onboarding) {
    return (
      <AppShell>
        <OnboardingWelcome name={profile?.name || "there"} />
      </AppShell>
    );
  }

  const { stats, attention, recent_activity, thresholds } = data;
  const totalAttention =
    attention.stale_analyses.count +
    attention.clients_never_analysed.count +
    attention.pending_quotes.count +
    attention.unread_messages;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
            Welcome back, {profile?.name ?? "there"}
          </h1>
          <p className="mt-1 text-[var(--sapling-medium-grey)]">
            {totalAttention === 0
              ? "You're all caught up. Nothing needs your attention right now."
              : `You have ${totalAttention} ${totalAttention === 1 ? "thing" : "things"} that need a look.`}
          </p>
        </div>

        {/* Quick actions */}
        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Button
            variant="outline"
            className="h-auto flex-col gap-2 py-5"
            onClick={() => router.push("/quick-analysis")}
          >
            <Leaf className="size-5 text-[var(--sapling-orange)]" />
            <span className="font-medium">New Analysis</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-2 py-5"
            onClick={() => router.push("/quick-blend")}
          >
            <FlaskConical className="size-5 text-[var(--sapling-orange)]" />
            <span className="font-medium">New Blend</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-2 py-5"
            onClick={() => router.push("/season-manager")}
          >
            <Calendar className="size-5 text-[var(--sapling-orange)]" />
            <span className="font-medium">New Programme</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-2 py-5"
            onClick={() => router.push("/quotes")}
          >
            <FileText className="size-5 text-[var(--sapling-orange)]" />
            <span className="font-medium">New Quote</span>
          </Button>
        </div>

        {/* Stats strip */}
        <div className="mb-6 flex flex-wrap gap-4 rounded-xl border bg-white p-5">
          <Stat label="Clients" value={stats.clients} />
          <div className="hidden sm:block border-l border-gray-200" />
          <Stat label="Farms" value={stats.farms} />
          <div className="hidden sm:block border-l border-gray-200" />
          <Stat label="Fields" value={stats.fields} />
          <div className="hidden sm:block border-l border-gray-200" />
          <Stat label="This month" value={stats.analyses_this_month} />
          <div className="hidden sm:block border-l border-gray-200" />
          <Stat label="Active progs" value={stats.active_programmes} />
          <div className="hidden sm:block border-l border-gray-200" />
          <Stat label="Pending Q" value={stats.pending_quotes} />
        </div>

        {/* Main two-column */}
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Attention column */}
          <div className="space-y-4 lg:col-span-2">
            <AttentionCard
              tone="warning"
              icon={Clock}
              title={`Fields overdue for testing (${thresholds.stale_analysis_months}+ months)`}
              count={attention.stale_analyses.count}
              emptyMessage="All your fields have recent analyses."
              viewAllHref="/records"
            >
              {attention.stale_analyses.preview.map((item) => (
                <Link
                  key={item.analysis_id}
                  href={item.client_id ? `/clients/${item.client_id}` : "/records"}
                  className="block rounded-lg border bg-gray-50/50 px-3 py-2 transition-colors hover:bg-orange-50 hover:border-[var(--sapling-orange)]/30"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-[var(--sapling-dark)]">
                        {item.customer || "—"}
                        {item.field && <span className="text-[var(--sapling-medium-grey)]"> · {item.field}</span>}
                      </div>
                      <div className="mt-0.5 text-xs text-[var(--sapling-medium-grey)]">
                        {item.crop || "Unknown crop"} · last tested {relativeTime(item.last_analysed_at)}
                      </div>
                    </div>
                    <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                      {Math.round(item.days_old / 30)}mo
                    </span>
                  </div>
                </Link>
              ))}
            </AttentionCard>

            <AttentionCard
              tone="info"
              icon={Users}
              title="Clients without a soil analysis"
              count={attention.clients_never_analysed.count}
              emptyMessage="Every client has at least one analysis on file."
              viewAllHref="/clients"
            >
              {attention.clients_never_analysed.preview.map((c) => (
                <Link
                  key={c.client_id}
                  href={`/clients/${c.client_id}`}
                  className="flex items-center justify-between rounded-lg border bg-gray-50/50 px-3 py-2 transition-colors hover:bg-blue-50 hover:border-blue-300"
                >
                  <span className="truncate text-sm font-medium text-[var(--sapling-dark)]">
                    {c.name}
                  </span>
                  <ChevronRight className="size-4 shrink-0 text-[var(--sapling-medium-grey)]" />
                </Link>
              ))}
            </AttentionCard>

            <AttentionCard
              tone="info"
              icon={FileText}
              title="Pending quotes"
              count={attention.pending_quotes.count}
              emptyMessage="No quotes are currently waiting on a response."
              viewAllHref="/quotes"
            >
              {attention.pending_quotes.preview.map((q) => (
                <Link
                  key={q.quote_id}
                  href={`/quotes/${q.quote_id}`}
                  className="block rounded-lg border bg-gray-50/50 px-3 py-2 transition-colors hover:bg-blue-50 hover:border-blue-300"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-[var(--sapling-dark)]">
                        {q.customer || "—"}
                      </div>
                      <div className="mt-0.5 truncate text-xs text-[var(--sapling-medium-grey)]">
                        {q.blend_name}
                      </div>
                    </div>
                    <span className="shrink-0 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                      {q.days_pending}d
                    </span>
                  </div>
                </Link>
              ))}
            </AttentionCard>

            {attention.unread_messages > 0 && (
              <Link
                href="/quotes"
                className="flex items-center justify-between rounded-xl border border-red-200 bg-white p-5 transition-colors hover:bg-red-50"
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-9 items-center justify-center rounded-lg bg-red-50 text-red-600">
                    <MessageSquare className="size-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-[var(--sapling-dark)]">
                      Unread quote messages
                    </h3>
                    <p className="text-xs text-[var(--sapling-medium-grey)]">
                      {attention.unread_messages} new{" "}
                      {attention.unread_messages === 1 ? "message" : "messages"} waiting
                    </p>
                  </div>
                </div>
                <ChevronRight className="size-5 text-[var(--sapling-medium-grey)]" />
              </Link>
            )}
          </div>

          {/* Recent activity column */}
          <div>
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Recent activity</CardTitle>
                  <Link
                    href="/records"
                    className="inline-flex items-center gap-0.5 text-xs font-medium text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-orange)]"
                  >
                    Records <ChevronRight className="size-3" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recent_activity.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 py-6 text-center">
                    <Inbox className="size-6 text-gray-300" />
                    <p className="text-sm text-[var(--sapling-medium-grey)]">
                      No activity yet.
                    </p>
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {recent_activity.map((item) => (
                      <li key={`${item.type}-${item.id}`}>
                        <Link
                          href={item.href}
                          className="flex items-start gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-gray-50"
                        >
                          <ActivityIcon type={item.type} />
                          <div className="min-w-0 flex-1">
                            <div className="truncate font-medium text-[var(--sapling-dark)]">
                              {item.title}
                            </div>
                            {item.subtitle && (
                              <div className="truncate text-xs text-[var(--sapling-medium-grey)]">
                                {item.subtitle}
                              </div>
                            )}
                          </div>
                          <span className="shrink-0 text-[10px] text-[var(--sapling-medium-grey)]">
                            {relativeTime(item.created_at)}
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
