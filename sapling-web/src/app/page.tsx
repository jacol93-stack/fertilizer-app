"use client";

/**
 * Home page — search-first.
 *
 * Single big command bar that jumps to anything (clients, analyses,
 * blends, quotes). One line of stats below for context. No shortcut
 * grid, no recent-activity list, no onboarding ladder — the top nav
 * handles navigation and the search handles everything else.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import {
  AlertTriangle,
  FileText,
  FlaskConical,
  Leaf,
  Loader2,
  Search,
  Users,
} from "lucide-react";

interface WorkbenchStats {
  clients: number;
  farms: number;
  fields: number;
  analyses_this_month: number;
  active_programmes: number;
  pending_quotes: number;
}

interface WorkbenchResponse {
  user: { id: string; name?: string; email?: string; role: string };
  stats: WorkbenchStats;
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

function CommandBar() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(0);

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

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, []);

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

export default function HomePage() {
  const { profile, isLoading: authLoading } = useAuth();
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

  if (loading || authLoading) {
    return (
      <AppShell>
        <div className="flex min-h-[60vh] items-center justify-center">
          <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="mx-auto max-w-3xl px-4 py-16 text-center">
          <AlertTriangle className="mx-auto size-6 text-amber-500" />
          <p className="mt-2 text-sm text-[var(--sapling-medium-grey)]">
            Couldn&apos;t reach the server. Refresh the page when you&apos;re back online.
          </p>
        </div>
      </AppShell>
    );
  }

  const stats = data?.stats;

  return (
    <AppShell>
      <div className="mx-auto flex min-h-[70vh] max-w-2xl flex-col justify-center px-4 py-10">
        <h1 className="mb-6 text-center text-lg text-[var(--sapling-dark)]">
          {greeting}
          {profile?.name ? `, ${profile.name}` : ""}
        </h1>

        <CommandBar />

        {stats && (
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-5 gap-y-1 text-xs text-[var(--sapling-medium-grey)]">
            <Stat n={stats.clients} label="clients" />
            <Stat n={stats.fields} label="fields" />
            <Stat n={stats.analyses_this_month} label="analyses this month" />
            <Stat n={stats.active_programmes} label="open programmes" />
            <Stat n={stats.pending_quotes} label="pending quotes" />
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Stat({ n, label }: { n: number; label: string }) {
  return (
    <span>
      <strong className="font-semibold text-[var(--sapling-dark)] tabular-nums">{n}</strong>{" "}
      {label}
    </span>
  );
}
