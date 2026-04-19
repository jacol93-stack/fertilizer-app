"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { MONTH_NAMES } from "@/lib/season-constants";
import { Plus, X } from "lucide-react";

export interface GrowthStage {
  stage_name: string;
  stage_order: number;
  month_start: number;
  month_end: number;
  n_pct: number;
  p_pct: number;
  k_pct: number;
}

export interface Correction {
  type: string;
  product?: string;
  rate: string;
  timing: string;
  reason: string;
  note?: string;
}

export interface NutrientExplanation {
  nutrient: string;
  base_req: number;
  final_target: number;
  notes: string[];
}

export interface CorrectiveTarget {
  nutrient: string;
  current_mg_kg: number;
  optimal_range: string;
  target_mg_kg: number;
  direction: "build-up" | "draw-down";
  gap_mg_kg: number;
  annual_corrective_kg_ha: number;
  estimated_seasons: number;
  note: string;
}

export interface BlockInfo {
  block_id: string;
  block_name: string;
  crop: string;
  crop_type?: string; // "perennial" | "annual"
  growth_stages: GrowthStage[];
  nutrient_targets: Array<{ Nutrient?: string; nutrient?: string; Target_kg_ha?: number; target_kg_ha?: number }>;
  accepted_methods: string[];
  corrections?: Correction[];
  nutrient_explanations?: NutrientExplanation[];
  corrective_targets?: CorrectiveTarget[];
  missing_corrective_data?: string[];
}

export interface UserApplication {
  block_id: string;
  month: number;
  method: string;
}

interface ScheduleReviewProps {
  blockInfo: BlockInfo[];
  onApplicationsChange: (apps: UserApplication[]) => void;
  onPlantingMonthsChange?: (months: Record<string, number>) => void;
  // Re-hydrate internal state from the parent on mount so the schedule
  // survives navigating to the Blends step and back. Parent owns the
  // canonical state (UserApplication[]), we own the per-block working
  // copy + UI toggles.
  initialApplications?: UserApplication[];
  initialPlantingMonths?: Record<string, number>;
}

const STAGE_COLORS = [
  "bg-emerald-200 text-emerald-800",
  "bg-sky-200 text-sky-800",
  "bg-amber-200 text-amber-800",
  "bg-purple-200 text-purple-800",
  "bg-rose-200 text-rose-800",
  "bg-cyan-200 text-cyan-800",
  "bg-lime-200 text-lime-800",
  "bg-orange-200 text-orange-800",
];

function monthInStage(month: number, stage: GrowthStage): boolean {
  const ms = stage.month_start;
  const me = stage.month_end;
  if (ms <= me) return month >= ms && month <= me;
  return month >= ms || month <= me; // wraps around year
}

function getStageForMonth(month: number, stages: GrowthStage[]): GrowthStage | null {
  for (const s of stages) {
    if (monthInStage(month, s)) return s;
  }
  return null;
}

function shiftMonth(month: number, offset: number): number {
  let m = ((month - 1 + offset) % 12) + 1;
  if (m <= 0) m += 12;
  return m;
}

function shiftStage(stage: GrowthStage, offset: number): GrowthStage {
  return {
    ...stage,
    month_start: shiftMonth(stage.month_start, offset),
    month_end: shiftMonth(stage.month_end, offset),
  };
}

export function ScheduleReview({
  blockInfo,
  onApplicationsChange,
  onPlantingMonthsChange,
  initialApplications,
  initialPlantingMonths,
}: ScheduleReviewProps) {
  // Planting month per block — seed from parent if it has prior state,
  // otherwise default to each crop's first stage start month.
  const [plantingMonths, setPlantingMonths] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    for (const bi of blockInfo) {
      init[bi.block_id] =
        initialPlantingMonths?.[bi.block_id] ?? (bi.growth_stages[0]?.month_start || 1);
    }
    return init;
  });

  // Track applications per block — re-hydrate from the flat
  // UserApplication[] the parent preserves across step navigation.
  const [appsByBlock, setAppsByBlock] = useState<Record<string, Array<{ month: number; method: string }>>>(() => {
    const init: Record<string, Array<{ month: number; method: string }>> = {};
    for (const bi of blockInfo) {
      init[bi.block_id] = [];
    }
    for (const a of initialApplications || []) {
      if (init[a.block_id]) {
        init[a.block_id].push({ month: a.month, method: a.method });
      }
    }
    return init;
  });

  // Shared-schedule mode: one application list broadcast to every block
  // instead of N per-block lists. When blocks share a programme they'll
  // be applied uniformly, so editing the schedule per block is busywork.
  // Feasible when every block accepts at least one method in common.
  const sharedMethods = useMemo(() => {
    if (blockInfo.length === 0) return [] as string[];
    const first = new Set(blockInfo[0].accepted_methods || []);
    for (let i = 1; i < blockInfo.length; i++) {
      const accepted = new Set(blockInfo[i].accepted_methods || []);
      for (const m of Array.from(first)) {
        if (!accepted.has(m)) first.delete(m);
      }
    }
    return Array.from(first);
  }, [blockInfo]);
  const canShareSchedule = blockInfo.length > 1 && sharedMethods.length > 0;

  // If we're re-hydrating from parent state and blocks disagree on apps,
  // start in per-block mode so we don't clobber the differences. Fresh
  // mounts (no prior state) default to shared when feasible.
  const initiallyShared = useMemo(() => {
    if (!canShareSchedule) return false;
    if (!initialApplications || initialApplications.length === 0) return true;
    const byBlock: Record<string, string[]> = {};
    for (const bi of blockInfo) byBlock[bi.block_id] = [];
    for (const a of initialApplications) {
      if (byBlock[a.block_id]) byBlock[a.block_id].push(`${a.month}|${a.method}`);
    }
    const sig = (list: string[]) => [...list].sort().join(",");
    const first = sig(byBlock[blockInfo[0].block_id] || []);
    return blockInfo.every((bi) => sig(byBlock[bi.block_id] || []) === first);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [sharedSchedule, setSharedSchedule] = useState<boolean>(initiallyShared);

  const emitChange = (updated: Record<string, Array<{ month: number; method: string }>>) => {
    const apps: UserApplication[] = [];
    for (const [blockId, list] of Object.entries(updated)) {
      for (const a of list) {
        apps.push({ block_id: blockId, month: a.month, method: a.method });
      }
    }
    onApplicationsChange(apps);
  };

  const addApplication = (blockId: string) => {
    const existing = appsByBlock[blockId] || [];
    // Find next unused month
    const usedMonths = new Set(existing.map((a) => a.month));
    let nextMonth = 1;
    for (let m = 1; m <= 12; m++) {
      if (!usedMonths.has(m)) { nextMonth = m; break; }
    }
    const defaultMethod = blockInfo.find((b) => b.block_id === blockId)?.accepted_methods[0] || "broadcast";
    const updated = { ...appsByBlock, [blockId]: [...existing, { month: nextMonth, method: defaultMethod }] };
    setAppsByBlock(updated);
    emitChange(updated);
  };

  const removeApplication = (blockId: string, idx: number) => {
    const updated = {
      ...appsByBlock,
      [blockId]: (appsByBlock[blockId] || []).filter((_, i) => i !== idx),
    };
    setAppsByBlock(updated);
    emitChange(updated);
  };

  const updateApplication = (blockId: string, idx: number, field: "month" | "method", value: number | string) => {
    const updated = {
      ...appsByBlock,
      [blockId]: (appsByBlock[blockId] || []).map((a, i) =>
        i === idx ? { ...a, [field]: value } : a
      ),
    };
    setAppsByBlock(updated);
    emitChange(updated);
  };

  // ─── Shared-schedule helpers ────────────────────────────────────────
  // Source of truth in shared mode is still `appsByBlock`, but every
  // block carries an identical list. Mutations broadcast across all
  // block ids so the per-block emitChange contract to the parent is
  // unchanged (the backend gets one UserApplication per block per month
  // as before — no API change needed).

  const sharedApps = useMemo(() => {
    if (!sharedSchedule || blockInfo.length === 0) return [] as Array<{ month: number; method: string }>;
    return appsByBlock[blockInfo[0].block_id] || [];
  }, [sharedSchedule, blockInfo, appsByBlock]);

  const broadcastApps = (next: Array<{ month: number; method: string }>) => {
    const updated: Record<string, Array<{ month: number; method: string }>> = {};
    for (const bi of blockInfo) {
      updated[bi.block_id] = next.map((a) => ({ ...a }));
    }
    setAppsByBlock(updated);
    emitChange(updated);
  };

  const addSharedApplication = () => {
    const used = new Set(sharedApps.map((a) => a.month));
    let nextMonth = 1;
    for (let m = 1; m <= 12; m++) {
      if (!used.has(m)) { nextMonth = m; break; }
    }
    const defaultMethod = sharedMethods[0] || "broadcast";
    broadcastApps([...sharedApps, { month: nextMonth, method: defaultMethod }]);
  };

  const removeSharedApplication = (idx: number) => {
    broadcastApps(sharedApps.filter((_, i) => i !== idx));
  };

  const updateSharedApplication = (idx: number, field: "month" | "method", value: number | string) => {
    broadcastApps(sharedApps.map((a, i) => (i === idx ? { ...a, [field]: value } : a)));
  };

  const handleToggleShared = (next: boolean) => {
    setSharedSchedule(next);
    // When enabling shared mode, broadcast whichever block already has
    // the most applications set up so we don't silently drop work.
    if (next) {
      const richest = blockInfo.reduce<Array<{ month: number; method: string }>>((acc, bi) => {
        const list = appsByBlock[bi.block_id] || [];
        return list.length > acc.length ? list : acc;
      }, []);
      // Filter methods that aren't accepted by every block
      const allowed = new Set(sharedMethods);
      const sanitized = richest
        .map((a) => ({ ...a, method: allowed.has(a.method) ? a.method : sharedMethods[0] || "broadcast" }));
      broadcastApps(sanitized);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">When & How to Fertilize</h3>
        <p className="text-sm text-muted-foreground">
          Choose which months to apply fertilizer and the method for each. The engine will distribute nutrients based on the crop&apos;s growth stages.
        </p>
      </div>

      {/* Shared-schedule toggle + panel. Default to shared when feasible
          (more than one block and at least one method accepted by every
          block). The schedule still saves per-block on the backend; this
          is a UX collapse only. */}
      {canShareSchedule && (
        <div className="rounded-xl border bg-white">
          <label className="flex cursor-pointer items-center gap-3 border-b px-4 py-3">
            <input
              type="checkbox"
              checked={sharedSchedule}
              onChange={(e) => handleToggleShared(e.target.checked)}
              className="size-4 accent-[var(--sapling-orange)]"
            />
            <div className="flex-1">
              <p className="text-sm font-medium text-[var(--sapling-dark)]">
                Same schedule for all blocks
              </p>
              <p className="text-xs text-muted-foreground">
                {blockInfo.length} blocks share this programme — edit one schedule that applies to all.
                Turn off if one block needs a different month or method.
              </p>
            </div>
          </label>

          {sharedSchedule && (
            <div className="space-y-2 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Fertilizer Applications ({sharedApps.length})
              </p>

              {sharedApps.length === 0 && (
                <p className="py-2 text-center text-xs text-muted-foreground">No applications added yet</p>
              )}

              {sharedApps
                .map((a, i) => ({ a, i }))
                .sort((x, y) => x.a.month - y.a.month)
                .map(({ a, i }) => (
                  <div key={i} className="flex items-center gap-2 rounded-lg border px-3 py-2">
                    <select
                      value={a.month}
                      onChange={(e) => updateSharedApplication(i, "month", parseInt(e.target.value))}
                      className="rounded border bg-white px-2 py-1 text-sm font-medium"
                    >
                      {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => (
                        <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                      ))}
                    </select>
                    <select
                      value={a.method}
                      onChange={(e) => updateSharedApplication(i, "method", e.target.value)}
                      className="rounded border bg-white px-2 py-1 text-sm"
                    >
                      {sharedMethods.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => removeSharedApplication(i)}
                      className="ml-auto rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
                    >
                      <X className="size-3.5" />
                    </button>
                  </div>
                ))}

              <Button variant="outline" size="sm" onClick={addSharedApplication} className="w-full">
                <Plus className="size-3.5" />
                Add Application
              </Button>
            </div>
          )}
        </div>
      )}

      {blockInfo.map((bi) => {
        const blockApps = appsByBlock[bi.block_id] || [];
        const plantMonth = plantingMonths[bi.block_id] || bi.growth_stages[0]?.month_start || 1;
        const defaultStart = bi.growth_stages[0]?.month_start || 1;
        const offset = plantMonth - defaultStart;

        // Shift all stages by offset
        const shiftedStages = bi.growth_stages.map((s) => shiftStage(s, offset));

        return (
          <div key={bi.block_id} className="rounded-xl border bg-white">
            {/* Block header */}
            <div className="flex items-center justify-between border-b px-4 py-3">
              <div>
                <p className="font-semibold text-[var(--sapling-dark)]">{bi.block_name}</p>
                <p className="text-xs text-muted-foreground">{bi.crop}</p>
              </div>
              {bi.crop_type !== "perennial" && (
                <div className="flex items-center gap-2">
                  <label className="text-xs font-medium text-muted-foreground">Planting month:</label>
                  <select
                    value={plantMonth}
                    onChange={(e) => {
                      const newMonth = parseInt(e.target.value);
                      const updated = { ...plantingMonths, [bi.block_id]: newMonth };
                      setPlantingMonths(updated);
                      onPlantingMonthsChange?.(updated);
                    }}
                    className="rounded border bg-white px-2 py-1 text-sm font-medium"
                  >
                    {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => (
                      <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Soil corrections */}
            {bi.corrections && bi.corrections.length > 0 && (
              <div className="mx-4 mt-3 space-y-2">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Soil Corrections Required</p>
                {bi.corrections.map((c, i) => (
                  <div key={i} className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                    <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      c.type === "lime" ? "bg-amber-200 text-amber-800" :
                      c.type === "gypsum" ? "bg-blue-200 text-blue-800" :
                      "bg-green-200 text-green-800"
                    }`}>
                      {c.type === "organic_matter" ? "Org C" : c.type}
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-medium text-[var(--sapling-dark)]">
                        {c.product ? `${c.product} — ${c.rate}` : c.note || c.rate}
                      </p>
                      <p className="text-[10px] text-muted-foreground">{c.timing} &middot; {c.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Nutrient explanations */}
            {bi.nutrient_explanations && bi.nutrient_explanations.length > 0 && (
              <div className="mx-4 mt-2 space-y-1">
                {bi.nutrient_explanations.map((ex) => (
                  <div key={ex.nutrient} className="text-[10px] text-muted-foreground">
                    {ex.notes.map((note, i) => (
                      <p key={i}>
                        <span className="font-medium text-[var(--sapling-dark)]">{ex.nutrient}</span>: {note}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {/* Missing corrective data banner */}
            {bi.missing_corrective_data && bi.missing_corrective_data.length > 0 && (
              <div className="mx-4 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                <p className="text-xs text-amber-800">
                  <span className="font-medium">Soil correction plan unavailable</span> — missing{" "}
                  <strong>{bi.missing_corrective_data.join(", ")}</strong> from soil analysis.
                  These values are needed to calculate corrective fertilizer rates and timelines.
                </p>
              </div>
            )}

            {/* Soil correction plan */}
            {bi.corrective_targets && bi.corrective_targets.length > 0 && (
              <div className="mx-4 mt-3">
                <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Soil Correction Plan
                </p>
                <div className="space-y-1">
                  {bi.corrective_targets.map((ct) => (
                    <div
                      key={ct.nutrient}
                      className={`rounded-lg border px-3 py-2 text-xs ${
                        ct.direction === "build-up"
                          ? "border-blue-200 bg-blue-50 text-blue-800"
                          : "border-orange-200 bg-orange-50 text-orange-800"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{ct.nutrient}</span>
                        <span className="text-[10px]">
                          {ct.current_mg_kg} → {ct.target_mg_kg} mg/kg (optimal {ct.optimal_range})
                        </span>
                      </div>
                      <p className="mt-0.5 text-[10px]">
                        {ct.direction === "build-up"
                          ? `~${ct.estimated_seasons} season${ct.estimated_seasons !== 1 ? "s" : ""} at ${ct.annual_corrective_kg_ha} kg/ha above maintenance`
                          : `~${ct.estimated_seasons} season${ct.estimated_seasons !== 1 ? "s" : ""} at reduced application`
                        }
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Planting window warning */}
            {offset !== 0 && (
              <div className="mx-4 mt-3 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                <p className="text-xs text-amber-800">
                  Standard SA planting for {bi.crop} is <strong>{MONTH_NAMES[defaultStart]}</strong>.
                  You selected <strong>{MONTH_NAMES[plantMonth]}</strong> — all growth stages will shift by {Math.abs(offset)} month{Math.abs(offset) !== 1 ? "s" : ""} {offset > 0 ? "later" : "earlier"}.
                </p>
                <div className="flex gap-2 ml-3 shrink-0">
                  <button
                    onClick={() => {
                      const updated = { ...plantingMonths, [bi.block_id]: defaultStart };
                      setPlantingMonths(updated);
                      onPlantingMonthsChange?.(updated);
                    }}
                    className="rounded px-2 py-1 text-[10px] font-medium text-amber-700 hover:bg-amber-100"
                  >
                    Reset
                  </button>
                  <button
                    className="rounded bg-amber-600 px-2 py-1 text-[10px] font-medium text-white hover:bg-amber-700"
                    onClick={() => {}} // Already accepted by selecting
                  >
                    OK
                  </button>
                </div>
              </div>
            )}

            {/* Growth stage timeline */}
            <div className="px-4 py-3">
              <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Growth Stages</p>
              <div className="flex gap-0.5 rounded-lg overflow-hidden">
                {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => {
                  const stage = getStageForMonth(m, shiftedStages);
                  const stageIdx = stage ? shiftedStages.indexOf(stage) : -1;
                  const colorClass = stageIdx >= 0 ? STAGE_COLORS[stageIdx % STAGE_COLORS.length] : "bg-gray-100 text-gray-400";
                  const hasApp = blockApps.some((a) => a.month === m);
                  const isPlanting = m === plantMonth;

                  return (
                    <div
                      key={m}
                      className={`flex-1 py-1.5 text-center text-[10px] font-medium ${colorClass} ${hasApp ? "ring-2 ring-[var(--sapling-orange)] ring-inset" : ""} ${isPlanting ? "border-b-2 border-black" : ""}`}
                      title={stage?.stage_name || "No stage"}
                    >
                      {MONTH_NAMES[m]?.slice(0, 3)}
                    </div>
                  );
                })}
              </div>
              {/* Stage names aligned under their months */}
              <div className="relative mt-0.5 flex gap-0.5">
                {(() => {
                  // Build spans: for each stage, find its start/end column positions
                  const cells: Array<{ stage: GrowthStage; stageIdx: number; startCol: number; span: number }> = [];
                  let prevStageIdx = -1;
                  let currentStart = 0;
                  let currentSpan = 0;

                  for (let m = 1; m <= 12; m++) {
                    const stage = getStageForMonth(m, shiftedStages);
                    const idx = stage ? shiftedStages.indexOf(stage) : -1;
                    if (idx !== prevStageIdx) {
                      if (prevStageIdx >= 0 && currentSpan > 0) {
                        cells.push({ stage: shiftedStages[prevStageIdx], stageIdx: prevStageIdx, startCol: currentStart, span: currentSpan });
                      }
                      currentStart = m - 1;
                      currentSpan = idx >= 0 ? 1 : 0;
                      prevStageIdx = idx;
                    } else if (idx >= 0) {
                      currentSpan++;
                    }
                  }
                  if (prevStageIdx >= 0 && currentSpan > 0) {
                    cells.push({ stage: shiftedStages[prevStageIdx], stageIdx: prevStageIdx, startCol: currentStart, span: currentSpan });
                  }

                  return cells.map((c) => (
                    <div
                      key={`${c.stage.stage_name}-${c.startCol}`}
                      className={`overflow-hidden text-center text-[9px] font-medium leading-tight py-0.5 rounded-sm ${STAGE_COLORS[c.stageIdx % STAGE_COLORS.length].split(" ")[0]} ${STAGE_COLORS[c.stageIdx % STAGE_COLORS.length].split(" ")[1]}`}
                      style={{
                        position: "absolute",
                        left: `${(c.startCol / 12) * 100}%`,
                        width: `${(c.span / 12) * 100}%`,
                      }}
                      title={c.stage.stage_name}
                    >
                      {c.stage.stage_name}
                    </div>
                  ));
                })()}
                {/* Spacer for height */}
                <div className="h-4 w-full" />
              </div>
            </div>

            {/* Applications — hidden when the shared-schedule panel
                above is driving every block. Per-block planting month
                and growth timeline stay visible because those are about
                the block itself, not the application schedule. */}
            {!sharedSchedule && (
              <div className="border-t px-4 py-3 space-y-2">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Fertilizer Applications ({blockApps.length})
                </p>

                {blockApps.length === 0 && (
                  <p className="py-2 text-center text-xs text-muted-foreground">No applications added yet</p>
                )}

                {blockApps
                  .sort((a, b) => a.month - b.month)
                  .map((app, idx) => {
                    const stage = getStageForMonth(app.month, shiftedStages);
                    return (
                      <div key={idx} className="flex items-center gap-2 rounded-lg border px-3 py-2">
                        <select
                          value={app.month}
                          onChange={(e) => updateApplication(bi.block_id, idx, "month", parseInt(e.target.value))}
                          className="rounded border bg-white px-2 py-1 text-sm font-medium"
                        >
                          {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => (
                            <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                          ))}
                        </select>
                        <select
                          value={app.method}
                          onChange={(e) => updateApplication(bi.block_id, idx, "method", e.target.value)}
                          className="rounded border bg-white px-2 py-1 text-sm"
                        >
                          {bi.accepted_methods.map((m) => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                        {stage && (
                          <span className="text-xs text-muted-foreground">{stage.stage_name}</span>
                        )}
                        <button
                          onClick={() => removeApplication(bi.block_id, idx)}
                          className="ml-auto rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
                        >
                          <X className="size-3.5" />
                        </button>
                      </div>
                    );
                  })}

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addApplication(bi.block_id)}
                  className="w-full"
                >
                  <Plus className="size-3.5" />
                  Add Application
                </Button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
