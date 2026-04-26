"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import {
  Calendar,
  ChevronRight,
  Sparkles,
} from "lucide-react";

import { listProgrammes } from "@/lib/programmes-v2";
import { ProgrammeState, type ProgrammeListItem } from "@/lib/types/programme-artifact";

const STATE_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  approved: "bg-emerald-100 text-emerald-700",
  activated: "bg-green-100 text-green-700",
  in_progress: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
  archived: "bg-gray-100 text-gray-500",
};

const FILTER_STATES: Array<ProgrammeState | null> = [
  null,
  ProgrammeState.DRAFT,
  ProgrammeState.APPROVED,
  ProgrammeState.ACTIVATED,
  ProgrammeState.COMPLETED,
];

export default function SeasonManagerPageWrapper() {
  return (
    <Suspense>
      <SeasonManagerPage />
    </Suspense>
  );
}

function SeasonManagerPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [programmes, setProgrammes] = useState<ProgrammeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [stateFilter, setStateFilter] = useState<ProgrammeState | null>(null);

  // Redirect handoff from Quick Analysis to builder
  useEffect(() => {
    const isNew = searchParams.get("new");
    const analysisId = searchParams.get("analysis_id");
    if (isNew && analysisId) {
      router.replace(`/season-manager/new?analysis_id=${analysisId}`);
    }
  }, [searchParams, router]);

  useEffect(() => {
    listProgrammes({ limit: 100 })
      .then(setProgrammes)
      .catch(() => toast.error("Failed to load programmes"))
      .finally(() => setLoading(false));
  }, []);

  const visible = programmes.filter((p) => p.state !== "archived");
  const filtered = stateFilter
    ? visible.filter((p) => p.state === stateFilter)
    : visible;
  const active = visible.filter((p) =>
    p.state === "approved" || p.state === "activated" || p.state === "in_progress",
  );

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <Calendar className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Season Manager</h1>
            <p className="text-sm text-[var(--sapling-medium-grey)]">
              Build and manage full-season fertilizer programmes
            </p>
          </div>
        </div>

        <Card
          role="button"
          tabIndex={0}
          aria-label="Build a new programme"
          className="mb-8 cursor-pointer border-2 border-transparent transition-all hover:border-[var(--sapling-orange)] hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--sapling-orange)] focus-visible:ring-offset-2"
          onClick={() => router.push("/season-manager/new")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              router.push("/season-manager/new");
            }
          }}
        >
          <CardContent className="flex items-start gap-4 py-6">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-orange-100 text-[var(--sapling-orange)]">
              <Sparkles className="size-6" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-[var(--sapling-dark)]">New Programme</p>
              <p className="mt-1 text-sm text-muted-foreground">
                From soil analysis → nutrient targets → optimized blends, per block
              </p>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="space-y-3" aria-busy="true" aria-label="Loading programmes">
            {[0, 1, 2].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-4">
                    <div className="size-10 rounded-lg bg-muted" />
                    <div className="space-y-2">
                      <div className="h-4 w-40 rounded bg-muted" />
                      <div className="h-3 w-56 rounded bg-muted/70" />
                    </div>
                  </div>
                  <div className="size-5 rounded-full bg-muted" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : visible.length === 0 ? (
          <Card className="flex min-h-[200px] flex-col items-center justify-center text-center">
            <CardContent>
              <Calendar className="mx-auto mb-4 size-12 text-muted-foreground/30" />
              <p className="text-lg font-medium text-muted-foreground">No programmes yet</p>
              <p className="mt-1 text-sm text-muted-foreground/70">
                Create your first season programme to get started
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {active.length > 0 && (
              <div className="mb-8">
                <h2 className="mb-3 text-lg font-semibold text-[var(--sapling-dark)]">Active Programmes</h2>
                <div className="space-y-2">
                  {active.map((p) => (
                    <ProgrammeCard key={p.id} programme={p} accent="green" router={router} />
                  ))}
                </div>
              </div>
            )}

            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">All Programmes</h2>
                <div className="flex gap-1.5">
                  {FILTER_STATES.map((s) => (
                    <button
                      key={s || "all"}
                      onClick={() => setStateFilter(s)}
                      className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                        stateFilter === s
                          ? "bg-[var(--sapling-orange)] text-white"
                          : "bg-muted text-muted-foreground hover:bg-muted/80"
                      }`}
                    >
                      {s ? s.charAt(0).toUpperCase() + s.slice(1) : "All"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                {filtered.map((p) => (
                  <ProgrammeCard key={p.id} programme={p} accent="orange" router={router} />
                ))}
                {filtered.length === 0 && (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    No {stateFilter} programmes found
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

interface ProgrammeCardProps {
  programme: ProgrammeListItem;
  accent: "green" | "orange";
  router: ReturnType<typeof useRouter>;
}

function ProgrammeCard({ programme, accent, router }: ProgrammeCardProps) {
  const title = programme.farm_name
    ? `${programme.farm_name} — ${programme.crop}`
    : programme.crop;
  const goto = () => router.push(`/season-manager/artifact/${programme.id}`);
  const accentClass = accent === "green"
    ? "border-l-4 border-l-green-500"
    : "border-l-4 border-l-[var(--sapling-orange)]";

  return (
    <Card
      role="button"
      tabIndex={0}
      aria-label={`Open programme ${title}`}
      className={`cursor-pointer transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--sapling-orange)] focus-visible:ring-offset-2 ${accentClass}`}
      onClick={goto}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          goto();
        }
      }}
    >
      <CardContent className="flex items-center justify-between py-3">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <Sparkles className="size-4" />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--sapling-dark)]">{title}</p>
            <p className="text-xs text-muted-foreground">
              {programme.blocks_count} block{programme.blocks_count !== 1 ? "s" : ""} ·{" "}
              planting {new Date(programme.planting_date).toLocaleDateString()} ·{" "}
              built {new Date(programme.build_date).toLocaleDateString()}
              {programme.foliar_events_count > 0 && ` · ${programme.foliar_events_count} foliar`}
              {programme.risk_flags_count > 0 && ` · ${programme.risk_flags_count} risk flag${programme.risk_flags_count !== 1 ? "s" : ""}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATE_COLORS[programme.state] || STATE_COLORS.draft}`}>
            {programme.state}
          </span>
          <ChevronRight className="size-4 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}
