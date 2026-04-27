"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  BarChart3,
  FileText,
  FlaskConical,
  Settings,
  ShieldAlert,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

interface AdminCounts {
  deletedRecords?: number;
}

export function AdminPortalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [counts, setCounts] = useState<AdminCounts>({});

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api
          .get<{ total?: number; items?: unknown[] }>(`/api/admin/deleted?limit=1`)
          .catch(() => ({ total: 0 } as { total?: number }));
        if (!alive) return;
        setCounts({ deletedRecords: res.total ?? 0 });
      } catch {
        // counts are decorative
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const sections: Array<{
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    count?: number;
    badgeColor?: string;
  }> = [
    { href: "/admin/dashboard", label: "Overview", icon: BarChart3 },
    { href: "/admin/users", label: "Users", icon: Users },
    { href: "/admin/audit", label: "Activity", icon: Activity },
    { href: "/admin/ai-usage", label: "AI usage", icon: Sparkles },
    { href: "/admin/materials", label: "Materials", icon: FlaskConical },
    { href: "/admin/norms", label: "Crop norms", icon: FileText },
    { href: "/admin/markups", label: "Pricing rules", icon: Settings },
    { href: "/admin/quotes", label: "Quotes", icon: FileText },
    {
      href: "/admin/trash",
      label: "Soft-deleted",
      icon: Trash2,
      count: counts.deletedRecords,
      badgeColor:
        counts.deletedRecords && counts.deletedRecords > 0
          ? "bg-amber-100 text-amber-700"
          : undefined,
    },
  ];

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-4 py-6 lg:gap-8">
        <aside className="hidden w-60 shrink-0 lg:block">
          <Link
            href="/"
            className="mb-4 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-[var(--sapling-dark)]"
          >
            <ArrowLeft className="size-3.5" />
            Exit admin
          </Link>

          <div className="mb-4 rounded-lg border bg-white p-3">
            <div className="flex items-center gap-1.5">
              <ShieldAlert className="size-3.5 text-[var(--sapling-orange)]" />
              <span className="text-sm font-semibold text-[var(--sapling-dark)]">
                Admin
              </span>
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              System health, user activity, materials catalogue, soft-deleted
              recovery.
            </p>
          </div>

          <nav className="space-y-1">
            {sections.map(({ href, label, icon: Icon, count, badgeColor }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                    active
                      ? "bg-[var(--sapling-orange)] text-white"
                      : "text-[var(--sapling-dark)] hover:bg-orange-50"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Icon className="size-4" />
                    {label}
                  </span>
                  {typeof count === "number" && count > 0 && (
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium tabular-nums ${
                        active
                          ? "bg-white/20 text-white"
                          : badgeColor ?? "bg-muted text-muted-foreground"
                      }`}
                    >
                      {count}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </AppShell>
  );
}
