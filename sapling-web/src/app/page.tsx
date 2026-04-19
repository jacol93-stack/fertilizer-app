"use client";

/**
 * Home page — command bar + today list.
 *
 * One question: "what needs my attention right now, and how do I jump
 * to anything?" No stacked cards, no six-stat strip. Just:
 *   1. A big search input (focus-on-load, ⌘K / "/" to re-focus) that
 *      queries /api/workbench/search across clients, analyses, blends,
 *      and quotes. Arrow keys + Enter navigate results.
 *   2. A single "Today" list — stale tests, pending quotes, unread
 *      messages, and never-analysed clients merged and sorted by
 *      urgency server-side.
 *   3. A compact stats strip + quick-action buttons below.
 *
 * Onboarding (brand-new agent) keeps its dedicated welcome screen.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Calendar,
  ChevronRight,
  Clock,
  FileText,
  FlaskConical,
  Leaf,
  MessageSquare,
  Plus,
  Search,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────

interface WorkbenchStats {
  clients: number;
  farms: number;
  fields: number;
  analyses_this_month: number;
  active_programmes: number;
  pending_quotes: number;
}

type TodayKind =
  | "unread_messages"
  | "stale_analysis"
  | "pending_quote"
  | "never_analysed";

interface TodayItem {
  kind: TodayKind;
  urgency: number;
  title: string;
  subtitle: string;
  badge: string;
  href: string;
}

interface WorkbenchResponse {
  user: { id: string; name?: string; email?: string; role: string };
  stats: WorkbenchStats;
  today: TodayItem[];
  is_onboarding: boolean;
}

type SearchKind = "client" | "analysis" | "blend" | "quote";

interface SearchResult {
  kind: SearchKind;
  id: string;
  title: string;
  subtitle: string;
  href: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
}

// ── Icon + label maps ────────────────────────────────────────────────────

const TODAY_ICON: Record<TodayKind, React.ComponentType<{ className?: string }>> = {
  unread_messages: MessageSquare,
  stale_analysis: Clock,
  pending_quote: FileText,
  never_analysed: UserPlus,
};

const TODAY_TONE: Record<TodayKind, string> = {
  unread_messages: "bg-red-50 text-red-600",
  stale_analysis: "bg-amber-50 text-amber-600",
  pending_quote: "bg-blue-50 text-blue-600",
  never_analysed: "bg-gray-50 text-gray-600",
};

const SEARCH_ICON: Record<SearchKind, React.ComponentType<{ className?: string }>> = {
  client: Users,
  analysis: Leaf,
  blend: FlaskConical,
  quote: FileText,
};

const SEARCH_KIND_LABEL: Record<SearchKind, string> = {
  client: "Client",
  analysis: "Analysis",
  blend: "Blend",
  quote: "Quote",
};

// ── Command bar ──────────────────────────────────────────────────────────

function CommandBar() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(0);

  // Focus on mount + global shortcuts (⌘K, "/")
  useEffect(() => {
    inputRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      const inField = tag === "INPUT" || tag === "TEXTAREA";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      } else if (e.key === "/" && !inField) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Close results when clicking outside
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, []);

  // Debounced search
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const handle = setTimeout(async () => {
      try {
        const res = await api.get<SearchResponse>(
          `/api/workbench/search?q=${encodeURIComponent(q)}`,
        );
        setResults(res.results);
        setCursor(0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 150);
    return () => clearTimeout(handle);
  }, [query]);

  const go = useCallback(
    (href: string) => {
      setOpen(false);
      setQuery("");
      router.push(href);
    },
    [router],
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, Math.max(results.length - 1, 0)));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter") {
      if (results[cursor]) {
        e.preventDefault();
        go(results[cursor].href);
      }
    } else if (e.key === "Escape") {
      setQuery("");
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  const showDropdown = open && query.trim().length >= 2;

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-[var(--sapling-medium-grey)]" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Jump to a client, field, analysis, blend, or quote…"
          className="h-14 w-full rounded-xl border border-gray-200 bg-white pl-11 pr-20 text-base shadow-sm outline-none ring-0 transition-colors placeholder:text-[var(--sapling-medium-grey)] focus:border-[var(--sapling-orange)] focus:ring-2 focus:ring-[var(--sapling-orange)]/20"
          aria-label="Search"
          autoComplete="off"
        />
        <kbd className="absolute right-4 top-1/2 hidden -translate-y-1/2 rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 text-[11px] font-medium text-[var(--sapling-medium-grey)] sm:block">
          ⌘K
        </kbd>
      </div>

      {showDropdown && (
        <div className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg">
          {loading && results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-[var(--sapling-medium-grey)]">
              Searching…
            </div>
          ) : results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-[var(--sapling-medium-grey)]">
              No matches for &ldquo;{query.trim()}&rdquo;
            </div>
          ) : (
            <ul className="max-h-96 overflow-y-auto py-1">
              {results.map((r, i) => {
                const Icon = SEARCH_ICON[r.kind];
                const active = i === cursor;
                return (
                  <li key={`${r.kind}-${r.id}`}>
                    <button
                      type="button"
                      onMouseEnter={() => setCursor(i)}
                      onClick={() => go(r.href)}
                      className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                        active ? "bg-orange-50" : "hover:bg-gray-50"
                      }`}
                    >
                      <Icon className="size-4 shrink-0 text-[var(--sapling-medium-grey)]" />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-[var(--sapling-dark)]">
                          {r.title}
                        </div>
                        {r.subtitle && (
                          <div className="truncate text-xs text-[var(--sapling-medium-grey)]">
                            {r.subtitle}
                          </div>
                        )}
                      </div>
                      <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[var(--sapling-medium-grey)]">
                        {SEARCH_KIND_LABEL[r.kind]}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ── Today list row ───────────────────────────────────────────────────────

function TodayRow({ item }: { item: TodayItem }) {
  const Icon = TODAY_ICON[item.kind];
  const tone = TODAY_TONE[item.kind];
  return (
    <Link
      href={item.href}
      className="flex items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 transition-colors hover:border-gray-200 hover:bg-gray-50"
    >
      <div className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${tone}`}>
        <Icon className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-[var(--sapling-dark)]">
          {item.title}
        </div>
        <div className="truncate text-xs text-[var(--sapling-medium-grey)]">
          {item.subtitle}
        </div>
      </div>
      <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-[var(--sapling-dark)]">
        {item.badge}
      </span>
      <ChevronRight className="size-4 shrink-0 text-[var(--sapling-medium-grey)]" />
    </Link>
  );
}

// ── Skeleton + error + onboarding ────────────────────────────────────────

function HomeSkeleton() {
  return (
    <div className="mx-auto max-w-3xl animate-pulse space-y-6 px-4 py-10">
      <div className="h-14 rounded-xl bg-gray-100" />
      <div className="h-64 rounded-xl bg-gray-100" />
      <div className="h-16 rounded-xl bg-gray-100" />
    </div>
  );
}

function HomeError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12 text-center">
      <AlertTriangle className="mx-auto size-8 text-amber-500" />
      <h2 className="mt-3 text-lg font-semibold text-[var(--sapling-dark)]">
        Couldn&apos;t reach the server
      </h2>
      <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
        Check your connection and try again in a moment.
      </p>
      <Button onClick={onRetry} variant="outline" className="mt-4">
        Retry
      </Button>
    </div>
  );
}

function OnboardingWelcome({ name }: { name: string }) {
  const steps = [
    {
      icon: Users,
      title: "Add your first client",
      body: "Create a client record so you can attach farms, fields, analyses and reports.",
      href: "/clients",
      cta: "Add client",
    },
    {
      icon: Leaf,
      title: "Run a soil analysis",
      body: "Enter lab values or upload a lab PDF to get classification, targets and a feeding plan.",
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

// ── Main page ────────────────────────────────────────────────────────────

export default function HomePage() {
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

  const greeting = useMemo(() => {
    const hr = new Date().getHours();
    if (hr < 12) return "Good morning";
    if (hr < 17) return "Good afternoon";
    return "Good evening";
  }, []);

  if (loading) {
    return (
      <AppShell>
        <HomeSkeleton />
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <HomeError onRetry={load} />
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

  const { stats, today } = data;

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl px-4 py-10">
        {/* Greeting */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">
            {greeting}, {profile?.name ?? "there"}
          </h1>
          <p className="mt-0.5 text-sm text-[var(--sapling-medium-grey)]">
            {today.length === 0
              ? "You're all caught up — nothing needs attention."
              : `${today.length} ${today.length === 1 ? "item" : "items"} need a look.`}
          </p>
        </div>

        {/* Command bar */}
        <CommandBar />

        {/* Today */}
        <section className="mt-8">
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--sapling-medium-grey)]">
              Today
            </h2>
            {today.length > 0 && (
              <Link
                href="/records"
                className="text-xs font-medium text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-orange)]"
              >
                All records →
              </Link>
            )}
          </div>
          {today.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-200 bg-white px-4 py-8 text-center">
              <Sparkles className="mx-auto size-5 text-[var(--sapling-orange)]" />
              <p className="mt-2 text-sm text-[var(--sapling-medium-grey)]">
                Nothing overdue. Start something new below.
              </p>
            </div>
          ) : (
            <div className="rounded-xl border bg-white p-1">
              {today.map((item, i) => (
                <TodayRow key={`${item.kind}-${i}`} item={item} />
              ))}
            </div>
          )}
        </section>

        {/* Quick actions */}
        <section className="mt-6 grid gap-2 sm:grid-cols-4">
          <Button
            variant="outline"
            className="h-auto flex-col gap-1.5 py-4"
            onClick={() => router.push("/quick-analysis")}
          >
            <Leaf className="size-5 text-[var(--sapling-orange)]" />
            <span className="text-sm font-medium">New analysis</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-1.5 py-4"
            onClick={() => router.push("/quick-blend")}
          >
            <FlaskConical className="size-5 text-[var(--sapling-orange)]" />
            <span className="text-sm font-medium">New blend</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-1.5 py-4"
            onClick={() => router.push("/season-manager")}
          >
            <Calendar className="size-5 text-[var(--sapling-orange)]" />
            <span className="text-sm font-medium">New programme</span>
          </Button>
          <Button
            variant="outline"
            className="h-auto flex-col gap-1.5 py-4"
            onClick={() => router.push("/quotes")}
          >
            <FileText className="size-5 text-[var(--sapling-orange)]" />
            <span className="text-sm font-medium">New quote</span>
          </Button>
        </section>

        {/* Compact stats footer */}
        <section className="mt-6 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-t border-gray-200 pt-4 text-xs text-[var(--sapling-medium-grey)]">
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">{stats.clients}</strong>{" "}
            clients
          </span>
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">{stats.farms}</strong>{" "}
            farms
          </span>
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">{stats.fields}</strong>{" "}
            fields
          </span>
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">
              {stats.analyses_this_month}
            </strong>{" "}
            analyses this month
          </span>
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">
              {stats.active_programmes}
            </strong>{" "}
            active programmes
          </span>
          <span>
            <strong className="font-semibold text-[var(--sapling-dark)]">
              {stats.pending_quotes}
            </strong>{" "}
            pending quotes
          </span>
        </section>
      </div>
    </AppShell>
  );
}
