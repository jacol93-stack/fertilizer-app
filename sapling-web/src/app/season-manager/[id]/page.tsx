"use client";

import { useState, useEffect, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Calendar,
  ChevronLeft,
  Loader2,
  Play,
  Trash2,
  Upload,
  AlertTriangle,
} from "lucide-react";

import { RecordApplication } from "@/components/season-manager/record-application";
import { VarianceView } from "@/components/season-manager/variance-view";
import { AdjustmentsView } from "@/components/season-manager/adjustments-view";
import { PlanEditor } from "@/components/season-manager/plan-editor";
import { ComparisonView } from "@/components/season-manager/comparison-view";
import { STATUS_COLORS, GROUP_COLORS, MONTH_NAMES } from "@/lib/season-constants";
import type { Programme, Block, ProgrammeBlend } from "@/lib/season-constants";

// Per-group heterogeneity report emitted by /api/programmes/:id/generate.
// Not persisted — regenerate to refresh. See Wilding (1985) derivation in
// services/programme_engine.HETEROGENEITY_THRESHOLDS.
interface GroupHeterogeneity {
  per_nutrient?: Record<string, { cv_pct: number | null; n: number; level: "ok" | "warn" | "split" }>;
  warnings?: Array<{ nutrient: string; cv_pct: number | null; level: "warn" | "split"; threshold_pct: number }>;
  any_warn?: boolean;
  any_split?: boolean;
  citation?: string;
}

// Extended type for detail page (blocks + blends come together)
interface ProgrammeDetail {
  id: string;
  name: string;
  season: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  client_id: string | null;
  farm_id: string | null;
  notes: string | null;
  blocks: (Block & { id: string; feeding_plan_id?: string | null; blend_group?: string | null; nutrient_targets?: unknown[] | null })[];
  blends: ProgrammeBlend[];
  heterogeneity_by_group?: Record<string, GroupHeterogeneity>;
}

export default function ProgrammeTrackerPageWrapper() {
  return (
    <Suspense>
      <ProgrammeTrackerPage />
    </Suspense>
  );
}

function ProgrammeTrackerPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isAdmin = useEffectiveAdmin();
  const programmeId = params.id as string;

  const [programme, setProgramme] = useState<ProgrammeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState(() => {
    const t = searchParams.get("tab");
    return t && ["overview", "edit", "applications", "adjustments", "compare", "variance"].includes(t)
      ? t
      : "overview";
  });

  const loadProgramme = () => {
    api.get<ProgrammeDetail>(`/api/programmes/${programmeId}`)
      .then(setProgramme)
      .catch((e) => {
        toast.error(e instanceof Error ? e.message : "Failed to load programme");
        router.push("/season-manager");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadProgramme(); }, [programmeId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const result = await api.post<ProgrammeDetail>(`/api/programmes/${programmeId}/generate`);
      setProgramme(result);
      toast.success("Programme generated successfully");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this programme? This cannot be undone.")) return;
    try {
      await api.post(`/api/programmes/${programmeId}/delete`);
      toast.success("Programme deleted");
      router.push("/season-manager");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await api.patch(`/api/programmes/${programmeId}`, { status: newStatus });
      setProgramme((prev) => prev ? { ...prev, status: newStatus } : prev);
      toast.success(`Programme ${newStatus}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Update failed");
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex min-h-[400px] items-center justify-center">
          <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
        </div>
      </AppShell>
    );
  }

  if (!programme) return null;

  const blocksWithoutTargets = programme.blocks.filter(
    (b) => !b.nutrient_targets || (Array.isArray(b.nutrient_targets) && b.nutrient_targets.length === 0)
  );
  const uniqueGroups = [...new Set(programme.blocks.map((b) => b.blend_group).filter(Boolean))] as string[];

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "edit", label: "Edit Plan" },
    { key: "applications", label: "Applications" },
    { key: "adjustments", label: "Adjustments" },
    { key: "compare", label: "Compare" },
    { key: "variance", label: "Variance" },
  ];

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Button variant="ghost" size="sm" onClick={() => router.push("/season-manager")} className="mb-3">
            <ChevronLeft className="size-4" />
            Back to Season Manager
          </Button>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
                <Calendar className="size-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">{programme.name}</h1>
                <p className="text-sm text-muted-foreground">
                  {programme.season && `${programme.season} · `}
                  {programme.blocks.length} blocks · Created {new Date(programme.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_COLORS[programme.status]}`}>
                {programme.status}
              </span>
              {programme.status === "draft" && (
                <Button size="sm" onClick={() => handleStatusChange("active")} className="bg-green-600 text-white hover:bg-green-700">
                  Activate
                </Button>
              )}
              {programme.status === "active" && (
                <Button size="sm" variant="outline" onClick={() => handleStatusChange("completed")}>
                  Complete
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={handleDelete}>
                <Trash2 className="size-4 text-red-500" />
              </Button>
            </div>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="mb-6 flex gap-1 rounded-lg bg-muted p-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ═══════════ OVERVIEW TAB ═══════════ */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Warning if blocks missing targets */}
            {blocksWithoutTargets.length > 0 && (
              <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
                <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" />
                <div>
                  <p className="font-medium text-amber-800">Blocks missing soil analysis</p>
                  <p className="mt-0.5 text-sm text-amber-700">
                    {blocksWithoutTargets.map((b) => b.name).join(", ")} — upload lab results or link a soil analysis.
                  </p>
                </div>
              </div>
            )}

            {/* Heterogeneity summary — surfaced right after generate, lives
                in client state only (not persisted). Regenerate to refresh. */}
            {programme.heterogeneity_by_group && (() => {
              const entries = Object.entries(programme.heterogeneity_by_group).filter(
                ([, h]) => h?.any_warn || h?.any_split
              );
              if (entries.length === 0) return null;
              const hasSplit = entries.some(([, h]) => h?.any_split);
              return (
                <div className={`flex items-start gap-3 rounded-lg border p-4 ${
                  hasSplit ? "border-red-200 bg-red-50" : "border-orange-200 bg-orange-50"
                }`}>
                  <AlertTriangle className={`mt-0.5 size-5 shrink-0 ${
                    hasSplit ? "text-red-600" : "text-orange-600"
                  }`} />
                  <div className="space-y-1">
                    <p className={`font-medium ${hasSplit ? "text-red-800" : "text-orange-800"}`}>
                      {hasSplit
                        ? "Blend group(s) span very different blocks"
                        : "Blend group(s) show block-to-block variation"}
                    </p>
                    <p className={`text-sm ${hasSplit ? "text-red-700" : "text-orange-700"}`}>
                      {entries.map(([g, h]) => {
                        const nuts = (h.warnings || [])
                          .map((w) => `${w.nutrient} CV ${w.cv_pct?.toFixed(0) ?? "?"}%`)
                          .join(", ");
                        return `Group ${g}: ${nuts}`;
                      }).join(" · ")}
                    </p>
                    <p className="text-xs italic text-muted-foreground">
                      Thresholds from {entries[0]?.[1]?.citation || "Wilding (1985)"}. Review whether
                      {hasSplit ? " splitting the group" : " a single uniform blend"} fits these blocks.
                    </p>
                  </div>
                </div>
              );
            })()}

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => router.push(`/season-manager/${programmeId}/upload`)}>
                <Upload className="size-4" />
                Add Lab Results
              </Button>
              <Button
                onClick={handleGenerate}
                disabled={generating || blocksWithoutTargets.length > 0}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {generating ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
                {programme.blends.length > 0 ? "Regenerate Programme" : "Generate Programme"}
              </Button>
            </div>

            {/* Blocks grid */}
            <div>
              <h2 className="mb-3 text-lg font-semibold text-[var(--sapling-dark)]">Blocks</h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {programme.blocks.map((block) => {
                  const groupIdx = uniqueGroups.indexOf(block.blend_group || "");
                  const groupColor = groupIdx >= 0 ? GROUP_COLORS[groupIdx % GROUP_COLORS.length] : "";
                  return (
                    <Card key={block.id}>
                      <CardContent className="py-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-[var(--sapling-dark)]">{block.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {block.crop}{block.cultivar && ` — ${block.cultivar}`}
                            </p>
                          </div>
                          {block.blend_group && (
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${groupColor}`}>
                              Group {block.blend_group}
                            </span>
                          )}
                        </div>
                        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                          <div><span className="text-muted-foreground">Area:</span> {block.area_ha ? `${block.area_ha} ha` : "—"}</div>
                          <div><span className="text-muted-foreground">Yield:</span> {block.yield_target ? `${block.yield_target} ${block.yield_unit || ""}` : "—"}</div>
                          <div>
                            <span className="text-muted-foreground">Analysis:</span>{" "}
                            {block.soil_analysis_id ? (
                              <span className="text-green-600">Linked</span>
                            ) : block.nutrient_targets && Array.isArray(block.nutrient_targets) && block.nutrient_targets.length > 0 ? (
                              <span className="text-green-600">Has targets</span>
                            ) : (
                              <span className="text-amber-600">Missing</span>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Blend timeline */}
            {programme.blends.length > 0 && (
              <div>
                <h2 className="mb-3 text-lg font-semibold text-[var(--sapling-dark)]">Season Timeline</h2>
                {uniqueGroups.map((group, gi) => {
                  const groupBlends = programme.blends
                    .filter((b) => b.blend_group === group)
                    .sort((a, b) => (a.application_month || 0) - (b.application_month || 0));
                  const groupBlocks = programme.blocks.filter((b) => b.blend_group === group);
                  const totalArea = groupBlocks.reduce((s, b) => s + (b.area_ha || 0), 0);
                  const groupHeterogeneity = programme.heterogeneity_by_group?.[group];
                  const showWarning = groupHeterogeneity?.any_warn || groupHeterogeneity?.any_split;
                  const isSplit = groupHeterogeneity?.any_split;

                  return (
                    <Card key={group} className="mb-4">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">
                            <span className={`mr-2 rounded-full px-2 py-0.5 text-xs font-medium ${GROUP_COLORS[gi % GROUP_COLORS.length]}`}>
                              Group {group}
                            </span>
                            {groupBlocks.map((b) => b.name).join(", ")}
                          </CardTitle>
                          <span className="text-xs text-muted-foreground">{totalArea} ha total</span>
                        </div>
                        {showWarning && (
                          <div className={`mt-2 flex items-start gap-2 rounded border px-3 py-2 text-xs ${
                            isSplit
                              ? "border-red-200 bg-red-50 text-red-800"
                              : "border-orange-200 bg-orange-50 text-orange-800"
                          }`}>
                            <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                            <div className="space-y-0.5">
                              <p className="font-medium">
                                {isSplit
                                  ? "High variation between blocks — consider splitting"
                                  : "Moderate variation — review before committing"}
                              </p>
                              <p className="opacity-90">
                                {(groupHeterogeneity?.warnings || []).map((w) => (
                                  <span key={w.nutrient} className="mr-3 inline-block">
                                    {w.nutrient}: CV {w.cv_pct?.toFixed(0) ?? "—"}%
                                    <span className="ml-1 text-[10px] opacity-70">
                                      ({w.level === "split" ? "≥" : "≥"}{w.threshold_pct}% {w.level})
                                    </span>
                                  </span>
                                ))}
                              </p>
                              <p className="text-[10px] italic opacity-70">
                                Source: {groupHeterogeneity?.citation || "Wilding (1985)"}
                              </p>
                            </div>
                          </div>
                        )}
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b text-left">
                                <th className="pb-2 pr-4 font-medium text-muted-foreground">Month</th>
                                <th className="pb-2 pr-4 font-medium text-muted-foreground">Stage</th>
                                <th className="pb-2 pr-4 font-medium text-muted-foreground">Notation</th>
                                <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">Rate (kg/ha)</th>
                                <th className="pb-2 text-right font-medium text-muted-foreground">Total (kg)</th>
                              </tr>
                            </thead>
                            <tbody>
                              {groupBlends.map((blend) => (
                                <tr key={blend.id} className="border-b border-muted last:border-0">
                                  <td className="py-2 pr-4 font-medium">{blend.application_month ? MONTH_NAMES[blend.application_month] : "—"}</td>
                                  <td className="py-2 pr-4 text-muted-foreground">{blend.stage_name || "—"}</td>
                                  <td className="py-2 pr-4">{blend.sa_notation || "—"}</td>
                                  <td className="py-2 pr-4 text-right tabular-nums">{blend.rate_kg_ha?.toFixed(0) || "—"}</td>
                                  <td className="py-2 text-right tabular-nums">{blend.total_kg?.toFixed(0) || "—"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ═══════════ EDIT TAB ═══════════ */}
        {activeTab === "edit" && (
          <PlanEditor programmeId={programmeId} onAfterSave={loadProgramme} />
        )}

        {/* ═══════════ APPLICATIONS TAB ═══════════ */}
        {activeTab === "applications" && (
          <RecordApplication
            programmeId={programmeId}
            blocks={programme.blocks as (Block & { id: string })[]}
          />
        )}

        {/* ═══════════ COMPARE TAB ═══════════ */}
        {activeTab === "compare" && (
          <ComparisonView programmeId={programmeId} />
        )}

        {/* ═══════════ VARIANCE TAB ═══════════ */}
        {activeTab === "variance" && (
          <VarianceView programmeId={programmeId} />
        )}

        {/* ═══════════ ADJUSTMENTS TAB ═══════════ */}
        {activeTab === "adjustments" && (
          <AdjustmentsView programmeId={programmeId} />
        )}
      </div>
    </AppShell>
  );
}
