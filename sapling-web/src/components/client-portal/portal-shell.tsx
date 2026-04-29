"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowLeft,
  LayoutGrid,
  Trees,
  FileText,
  CalendarDays,
  Activity,
  Upload,
  Settings,
  Plus,
  FlaskConical,
  FileBarChart,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

interface PortalCounts {
  farms: number;
  fields: number;
  documents: number;
  unlinkedDocuments: number;
  programmes: number;
  /** Earliest farm in the client — used to pre-fill the Build Programme link
   * with a sensible default farm so the wizard doesn't start blank. */
  firstFarm?: { id: string; name: string };
}

interface Client {
  id: string;
  name: string;
  contact_person?: string | null;
  email?: string | null;
  phone?: string | null;
}

export function ClientPortalShell({
  clientId,
  children,
}: {
  clientId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [client, setClient] = useState<Client | null>(null);
  const [counts, setCounts] = useState<PortalCounts | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [clients, farms, soil, leaf, programmes] = await Promise.all([
          api.getAll<Client>("/api/clients"),
          api.get<Array<{ id: string; name: string }>>(`/api/clients/${clientId}/farms`),
          api.getAll<{ field_id: string | null }>(`/api/soil?client_id=${clientId}`).catch(() => []),
          api.getAll<{ field_id: string | null }>(`/api/leaf?client_id=${clientId}`).catch(() => []),
          api.get<Array<{ id: string }>>(`/api/programmes/v2?client_id=${clientId}&limit=500`).catch(() => []),
        ]);
        if (!alive) return;
        const c = clients.find((cl) => cl.id === clientId) ?? null;
        setClient(c);

        const fieldsByFarm = await Promise.all(
          farms.map((f) =>
            api.get<Array<{ id: string }>>(`/api/clients/farms/${f.id}/fields`).catch(() => []),
          ),
        );
        const totalFields = fieldsByFarm.reduce((n, fs) => n + fs.length, 0);
        const unlinked = soil.filter((a) => !a.field_id).length + leaf.filter((a) => !a.field_id).length;
        if (!alive) return;
        setCounts({
          farms: farms.length,
          fields: totalFields,
          documents: soil.length + leaf.length,
          unlinkedDocuments: unlinked,
          programmes: programmes.length,
          firstFarm: farms[0] ? { id: farms[0].id, name: farms[0].name } : undefined,
        });
      } catch {
        // Counts are decorative — silent failure is fine.
      }
    })();
    return () => {
      alive = false;
    };
    // Re-fetch counts on every route change inside the client portal.
    // Without `pathname` in the dep list, navigating from /import back
    // to /overview leaves the sidebar stale — the user just bulk-
    // imported 16 fields but the FARMS / BLOCKS / PROGRAMMES strip
    // still reads the pre-import counts. Cheap (3 lightweight GETs)
    // and matches the user's mental model of "everything refreshes
    // when I click around".
  }, [clientId, pathname]);

  const buildProgrammeHref = (() => {
    const params = new URLSearchParams({ client_id: clientId });
    if (client?.name) params.set("client", client.name);
    if (counts?.firstFarm) {
      params.set("farm_id", counts.firstFarm.id);
      params.set("farm", counts.firstFarm.name);
    }
    return `/season-manager/new?${params.toString()}`;
  })();
  const newBlendHref = `/quick-blend?${client?.name ? `client=${encodeURIComponent(client.name)}&` : ""}client_id=${clientId}`;

  const sections: Array<{
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    count?: number;
    badgeColor?: string;
  }> = [
    { href: `/clients/${clientId}`, label: "Overview", icon: LayoutGrid },
    {
      href: `/clients/${clientId}/farms`,
      label: "Farms & Blocks",
      icon: Trees,
      count: counts?.fields,
    },
    {
      href: `/clients/${clientId}/documents`,
      label: "Documents",
      icon: FileText,
      count: counts?.documents,
      badgeColor:
        counts && counts.unlinkedDocuments > 0
          ? "bg-amber-100 text-amber-700"
          : undefined,
    },
    {
      href: `/clients/${clientId}/programmes`,
      label: "Programmes",
      icon: CalendarDays,
      count: counts?.programmes,
    },
    { href: `/clients/${clientId}/activity`, label: "Activity", icon: Activity },
  ];

  return (
    <AppShell>
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-4 py-6 lg:gap-8">
        <aside className="hidden w-60 shrink-0 lg:block">
          <Link
            href="/clients"
            className="mb-4 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-[var(--sapling-dark)]"
          >
            <ArrowLeft className="size-3.5" />
            All clients
          </Link>

          <div className="mb-4 rounded-lg border bg-white p-3">
            <div className="text-base font-semibold leading-tight text-[var(--sapling-dark)]">
              {client?.name ?? "Loading…"}
            </div>
            {client?.contact_person && (
              <div className="mt-1 text-xs text-muted-foreground">{client.contact_person}</div>
            )}
            {(client?.email || client?.phone) && (
              <div className="mt-1 truncate text-[11px] text-muted-foreground">
                {[client?.email, client?.phone].filter(Boolean).join(" · ")}
              </div>
            )}
            {counts && (
              <div className="mt-2.5 grid grid-cols-3 gap-1 border-t pt-2.5 text-center">
                <Stat label="Farms" value={counts.farms} />
                <Stat label="Blocks" value={counts.fields} />
                <Stat label="Programmes" value={counts.programmes} />
              </div>
            )}
          </div>

          <Link
            href={buildProgrammeHref}
            className="mb-3 flex items-center justify-center gap-1.5 rounded-md bg-[var(--sapling-orange)] px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--sapling-orange)]/90"
          >
            <Plus className="size-4" />
            Build Programme
          </Link>

          <nav className="space-y-1">
            {sections.map(({ href, label, icon: Icon, count, badgeColor }) => {
              const active =
                href === `/clients/${clientId}`
                  ? pathname === href
                  : pathname.startsWith(href);
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

          <div className="mt-5 space-y-0.5 border-t pt-3">
            <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Quick actions
            </p>
            <Link
              href={`/clients/${clientId}?action=add-farm`}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--sapling-dark)] transition-colors hover:bg-orange-50"
            >
              <Plus className="size-3.5" />
              Add farm
            </Link>
            <Link
              href={`/clients/${clientId}?action=upload`}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--sapling-dark)] transition-colors hover:bg-orange-50"
            >
              <Upload className="size-3.5" />
              Add soil / leaf analysis
            </Link>
            <Link
              href={`/clients/${clientId}/import`}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--sapling-dark)] transition-colors hover:bg-orange-50"
            >
              <Upload className="size-3.5" />
              Bulk import (CSV)
            </Link>
            <Link
              href={newBlendHref}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--sapling-dark)] transition-colors hover:bg-orange-50"
            >
              <FlaskConical className="size-3.5" />
              New blend
            </Link>
            <Link
              href={`/clients/${clientId}/soil-reports/new`}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--sapling-dark)] transition-colors hover:bg-orange-50"
            >
              <FileBarChart className="size-3.5" />
              New soil report
            </Link>
            <Link
              href={`/clients/${clientId}/settings`}
              className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-gray-50 hover:text-[var(--sapling-dark)]"
            >
              <Settings className="size-3.5" />
              Settings
            </Link>
          </div>
        </aside>

        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-sm font-semibold text-[var(--sapling-dark)] tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
    </div>
  );
}
