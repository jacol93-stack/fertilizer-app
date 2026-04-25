"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import {
  Calendar,
  Loader2,
  ChevronRight,
  Leaf,
  PencilRuler,
  Sparkles,
} from "lucide-react";

import type { Programme } from "@/lib/season-constants";
import { STATUS_COLORS } from "@/lib/season-constants";
import { listProgrammes } from "@/lib/programmes-v2";
import type { ProgrammeListItem } from "@/lib/types/programme-artifact";

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

  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<ProgrammeListItem[]>([]);
  const [artifactsLoading, setArtifactsLoading] = useState(true);

  // Redirect handoff from Quick Analysis to builder
  useEffect(() => {
    const isNew = searchParams.get("new");
    const analysisId = searchParams.get("analysis_id");
    if (isNew && analysisId) {
      router.replace(`/season-manager/new?analysis_id=${analysisId}`);
    }
  }, [searchParams, router]);

  useEffect(() => {
    api.getAll<Programme>("/api/programmes")
      .then(setProgrammes)
      .catch(() => toast.error("Failed to load programmes"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    listProgrammes({ limit: 50 })
      .then(setArtifacts)
      .catch(() => {
        // Silent: non-blocking — artifact list is additive, legacy list
        // is the primary surface during the bridge window.
      })
      .finally(() => setArtifactsLoading(false));
  }, []);

  const visibleArtifacts = artifacts.filter((a) => a.state !== "archived");

  const activeProgrammes = programmes.filter((p) => p.status === "active");
  const filteredProgrammes = statusFilter
    ? programmes.filter((p) => p.status === statusFilter)
    : programmes;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
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

        {/* CTA Cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2">
          <Card
            role="button"
            tabIndex={0}
            aria-label="Auto-Generate programme — recommended"
            className="cursor-pointer border-2 border-transparent transition-all hover:border-[var(--sapling-orange)] hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--sapling-orange)] focus-visible:ring-offset-2"
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
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-[var(--sapling-dark)]">Auto-Generate</p>
                  <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[var(--sapling-orange)]">
                    Recommended
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  From soil analysis → nutrient targets → optimized blends, per block
                </p>
              </div>
            </CardContent>
          </Card>

          <Card
            role="button"
            tabIndex={0}
            aria-label="Build programme manually — full control"
            className="cursor-pointer border-2 border-transparent transition-all hover:border-slate-500 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
            onClick={() => router.push("/season-manager/blank")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                router.push("/season-manager/blank");
              }
            }}
          >
            <CardContent className="flex items-start gap-4 py-6">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                <PencilRuler className="size-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-[var(--sapling-dark)]">Build Manually</p>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-600">
                    Full control
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  Define every application by hand — soil / leaf data drives validation if linked
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* New-engine artifacts — produced by the Build Artifact button
            on the wizard's Review step. Separate from legacy programmes
            during the bridge window (distinct table, distinct detail page). */}
        {!artifactsLoading && visibleArtifacts.length > 0 && (
          <div className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Full-Season Programmes</h2>
            </div>
            <div className="space-y-2">
              {visibleArtifacts.map((a) => (
                <Card
                  key={a.id}
                  className="cursor-pointer border-l-4 border-l-[var(--sapling-orange)] transition-shadow hover:shadow-md"
                  onClick={() => router.push(`/season-manager/artifact/${a.id}`)}
                >
                  <CardContent className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex size-8 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
                        <Sparkles className="size-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[var(--sapling-dark)]">
                          {a.farm_name || "(unnamed farm)"} — {a.crop}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {a.blocks_count} block{a.blocks_count !== 1 ? "s" : ""} ·{" "}
                          planting {new Date(a.planting_date).toLocaleDateString()} ·{" "}
                          built {new Date(a.build_date).toLocaleDateString()}
                          {a.foliar_events_count > 0 && ` · ${a.foliar_events_count} foliar`}
                          {a.risk_flags_count > 0 && ` · ${a.risk_flags_count} risk flag${a.risk_flags_count !== 1 ? "s" : ""}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-[var(--sapling-orange)]">
                        {a.state}
                      </span>
                      <ChevronRight className="size-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
          </div>
        ) : programmes.length === 0 ? (
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
            {/* Active Programmes */}
            {activeProgrammes.length > 0 && (
              <div className="mb-8">
                <h2 className="mb-3 text-lg font-semibold text-[var(--sapling-dark)]">Active Programmes</h2>
                <div className="space-y-3">
                  {activeProgrammes.map((prog) => {
                    const blocks = prog.programme_blocks || prog.blocks || [];
                    const cropList = [...new Set(blocks.map((b) => b.crop).filter(Boolean))];
                    return (
                      <Card
                        key={prog.id}
                        className="cursor-pointer border-l-4 border-l-green-500 transition-shadow hover:shadow-md"
                        onClick={() => router.push(`/season-manager/${prog.id}`)}
                      >
                        <CardContent className="flex items-center justify-between py-4">
                          <div className="flex items-center gap-4">
                            <div className="flex size-10 items-center justify-center rounded-lg bg-green-50 text-green-700">
                              <Leaf className="size-5" />
                            </div>
                            <div>
                              <p className="font-medium text-[var(--sapling-dark)]">{prog.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {blocks.length} block{blocks.length !== 1 ? "s" : ""}
                                {cropList.length > 0 && ` · ${cropList.join(", ")}`}
                                {prog.season && ` · ${prog.season}`}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                              Active
                            </span>
                            <ChevronRight className="size-4 text-muted-foreground" />
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* All Programmes */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">All Programmes</h2>
                <div className="flex gap-1.5">
                  {[null, "draft", "active", "completed", "archived"].map((status) => (
                    <button
                      key={status || "all"}
                      onClick={() => setStatusFilter(status)}
                      className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                        statusFilter === status
                          ? "bg-[var(--sapling-orange)] text-white"
                          : "bg-muted text-muted-foreground hover:bg-muted/80"
                      }`}
                    >
                      {status ? status.charAt(0).toUpperCase() + status.slice(1) : "All"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                {filteredProgrammes.map((prog) => {
                  const blocks = prog.programme_blocks || prog.blocks || [];
                  return (
                    <Card
                      key={prog.id}
                      className="cursor-pointer transition-shadow hover:shadow-md"
                      onClick={() => router.push(`/season-manager/${prog.id}`)}
                    >
                      <CardContent className="flex items-center justify-between py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex size-8 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
                            <Calendar className="size-4" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-[var(--sapling-dark)]">{prog.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {prog.season && `${prog.season} · `}
                              {blocks.length} block{blocks.length !== 1 ? "s" : ""} ·{" "}
                              {new Date(prog.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[prog.status] || STATUS_COLORS.draft}`}
                          >
                            {prog.status}
                          </span>
                          <ChevronRight className="size-4 text-muted-foreground" />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
                {filteredProgrammes.length === 0 && (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    No {statusFilter} programmes found
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
