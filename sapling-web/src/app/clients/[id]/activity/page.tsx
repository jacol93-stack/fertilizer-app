"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Activity as ActivityIcon,
  CalendarDays,
  FileText,
  Loader2,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api";

interface Item {
  id: string;
  type: "soil" | "leaf" | "programme" | "yield";
  date: string;
  title: string;
  subtitle?: string;
  href?: string;
}

export default function ActivityPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<Item[]>([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const [soils, leaves, programmes] = await Promise.all([
          api
            .getAll<Record<string, unknown>>(`/api/soil?client_id=${clientId}`)
            .catch(() => []),
          api
            .getAll<Record<string, unknown>>(`/api/leaf?client_id=${clientId}`)
            .catch(() => []),
          api
            .get<Record<string, unknown>[]>(`/api/programmes/v2?client_id=${clientId}&limit=200`)
            .catch(() => []),
        ]);
        if (!alive) return;
        const merged: Item[] = [];
        for (const s of soils) {
          merged.push({
            id: `soil-${s.id}`,
            type: "soil",
            date: (s.analysis_date as string) ?? (s.created_at as string),
            title: `Soil analysis · ${s.lab_name ?? "lab"}`,
            subtitle: [s.field, s.crop].filter(Boolean).join(" · "),
            href: `/clients/${clientId}/documents`,
          });
        }
        for (const l of leaves) {
          merged.push({
            id: `leaf-${l.id}`,
            type: "leaf",
            date: (l.sample_date as string) ?? (l.created_at as string),
            title: `Leaf analysis · ${l.lab_name ?? "lab"}`,
            subtitle: [l.field_id, l.crop].filter(Boolean).join(" · "),
            href: `/clients/${clientId}/documents`,
          });
        }
        for (const p of programmes) {
          merged.push({
            id: `prog-${p.id}`,
            type: "programme",
            date: (p.build_date as string) ?? (p.created_at as string),
            title: `Programme · ${p.ref_number ?? p.farm_name ?? "untitled"}`,
            subtitle: [p.crop, p.season].filter(Boolean).join(" · "),
            href: `/season-manager/artifact/${p.id}`,
          });
        }
        merged.sort((a, b) => b.date.localeCompare(a.date));
        setItems(merged);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [clientId]);

  const grouped = useMemo(() => {
    const out: Array<{ month: string; items: Item[] }> = [];
    let currentMonth = "";
    let bucket: Item[] = [];
    for (const item of items) {
      const d = new Date(item.date);
      const month = isNaN(d.getTime())
        ? "Unknown"
        : d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
      if (month !== currentMonth) {
        if (bucket.length > 0) out.push({ month: currentMonth, items: bucket });
        currentMonth = month;
        bucket = [];
      }
      bucket.push(item);
    }
    if (bucket.length > 0) out.push({ month: currentMonth, items: bucket });
    return out;
  }, [items]);

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
        <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Activity</h1>
        <p className="text-sm text-muted-foreground">
          {items.length} {items.length === 1 ? "event" : "events"} · most recent first
        </p>
      </div>

      {grouped.length === 0 ? (
        <div className="rounded-lg border border-dashed bg-white py-12 text-center">
          <ActivityIcon className="mx-auto size-8 text-muted-foreground/40" />
          <p className="mt-3 text-sm text-muted-foreground">
            No activity yet — upload an analysis or build a programme.
          </p>
        </div>
      ) : (
        grouped.map((group) => (
          <section key={group.month}>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {group.month}
            </h2>
            <ul className="space-y-1">
              {group.items.map((item) => (
                <li key={item.id}>
                  <Link
                    href={item.href ?? "#"}
                    className="flex items-center gap-3 rounded-md border bg-white px-3 py-2 text-sm transition-colors hover:bg-orange-50/40"
                  >
                    <Icon type={item.type} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium text-[var(--sapling-dark)]">
                        {item.title}
                      </span>
                      {item.subtitle && (
                        <span className="block truncate text-[11px] text-muted-foreground">
                          {item.subtitle}
                        </span>
                      )}
                    </span>
                    <span className="shrink-0 text-[11px] text-muted-foreground">
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}

function Icon({ type }: { type: Item["type"] }) {
  const cls = "size-3.5 shrink-0";
  switch (type) {
    case "soil":
      return <FileText className={`${cls} text-amber-600`} />;
    case "leaf":
      return <FileText className={`${cls} text-emerald-600`} />;
    case "programme":
      return <CalendarDays className={`${cls} text-orange-600`} />;
    case "yield":
      return <TrendingUp className={`${cls} text-blue-600`} />;
  }
}
