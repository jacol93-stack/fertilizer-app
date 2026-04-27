"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CalendarDays, Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";

interface ProgrammeArtifactSummary {
  id: string;
  ref_number?: string | null;
  prepared_for?: string | null;
  farm_name?: string | null;
  crop?: string | null;
  season?: string | null;
  state: string;
  build_date?: string | null;
  created_at: string;
}

const STATE_BADGE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  approved: "bg-emerald-50 text-emerald-700",
  activated: "bg-blue-50 text-blue-700",
  in_progress: "bg-orange-50 text-orange-700",
  completed: "bg-purple-50 text-purple-700",
  archived: "bg-gray-50 text-gray-400 line-through",
};

export default function ProgrammesPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;
  const [loading, setLoading] = useState(true);
  const [programmes, setProgrammes] = useState<ProgrammeArtifactSummary[]>([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const list = await api
          .get<ProgrammeArtifactSummary[]>(
            `/api/programmes/v2?client_id=${clientId}&limit=500`,
          )
          .catch(() => []);
        if (!alive) return;
        list.sort((a, b) => (b.build_date ?? b.created_at).localeCompare(a.build_date ?? a.created_at));
        setProgrammes(list);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [clientId]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Programmes</h1>
          <p className="text-sm text-muted-foreground">
            {programmes.length} {programmes.length === 1 ? "programme" : "programmes"}
          </p>
        </div>
        <Link
          href="/season-manager/new"
          className="inline-flex items-center gap-1.5 rounded-md bg-[var(--sapling-orange)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <Plus className="size-3.5" /> New programme
        </Link>
      </div>

      {programmes.length === 0 ? (
        <div className="rounded-lg border border-dashed bg-white py-12 text-center">
          <CalendarDays className="mx-auto size-8 text-muted-foreground/40" />
          <p className="mt-3 text-sm text-muted-foreground">No programmes yet for this client.</p>
        </div>
      ) : (
        <ul className="divide-y rounded-lg border bg-white">
          {programmes.map((p) => (
            <li key={p.id}>
              <Link
                href={`/season-manager/artifact/${p.id}`}
                className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-orange-50/50"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="truncate font-medium text-[var(--sapling-dark)]">
                      {p.ref_number || p.farm_name || "Untitled"}
                    </span>
                    {p.season && (
                      <span className="text-xs text-muted-foreground">· {p.season}</span>
                    )}
                  </div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                    {p.crop && <span>{p.crop}</span>}
                    {p.farm_name && <span>· {p.farm_name}</span>}
                    {p.build_date && (
                      <span>· built {new Date(p.build_date).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    STATE_BADGE[p.state] ?? "bg-gray-100 text-gray-600"
                  }`}
                >
                  {p.state.replace("_", " ")}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
