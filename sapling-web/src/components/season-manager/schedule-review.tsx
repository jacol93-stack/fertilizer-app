"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { MONTH_NAMES, methodLabel, seasonOrderIndex } from "@/lib/season-constants";

// Anchor at current month so applications later in the year sort before
// next-year ones when planning mid-season. Stable per render — built
// once at module load, fine for our cadence.
const SEASON_ANCHOR = new Date().getMonth() + 1;
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
  irrigation_type?: string | null;
  /** TRUE = injection unit installed, FALSE = irrigation but no
   * injection, NULL = unspecified (legacy fields). Drives whether the
   * engine offers fertigation. */
  fertigation_capable?: boolean | null;
  corrections?: Correction[];
  nutrient_explanations?: NutrientExplanation[];
  corrective_targets?: CorrectiveTarget[];
  missing_corrective_data?: string[];
  /** Set when this block has no soil analysis but the user attached it
   * to a group on the cluster step. Triggers the read-only "passenger"
   * presentation: stages copied from the group's mate, no editable
   * schedule of its own, and a pill explaining the inheritance. */
  inherited_from_group?: string;
  inherited_from_block_name?: string;
  block_area_ha?: number | null;
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

  // Drag-paint on the growth-stage strip fires pointer events faster than
  // React commits state, so closures over appsByBlock go stale mid-drag.
  // The ref mirrors the latest committed state AND is mutated synchronously
  // inside paintMonth so successive cells in the same drag see fresh data.
  const liveAppsRef = useRef(appsByBlock);
  useEffect(() => {
    liveAppsRef.current = appsByBlock;
  }, [appsByBlock]);

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

  // Click / drag-paint on the growth-stage strip. `action` is decided by
  // the gesture entry point (see GrowthStageStrip): click on an empty cell
  // → "add"; click on a populated cell → "remove"; subsequent cells in a
  // drag inherit the same action so the user paints uniformly. In shared
  // mode the change is broadcast across every block; in per-block mode it
  // mutates only the strip's own block.
  const paintMonth = (blockId: string, month: number, action: "add" | "remove") => {
    const prev = liveAppsRef.current;
    let updated: Record<string, Array<{ month: number; method: string }>>;
    if (sharedSchedule) {
      const cur = prev[blockInfo[0].block_id] || [];
      let next: Array<{ month: number; method: string }>;
      if (action === "add") {
        if (cur.some((a) => a.month === month)) return;
        const defaultMethod = sharedMethods[0] || "broadcast";
        next = [...cur, { month, method: defaultMethod }];
      } else {
        if (!cur.some((a) => a.month === month)) return;
        next = cur.filter((a) => a.month !== month);
      }
      updated = {};
      for (const bi of blockInfo) updated[bi.block_id] = next.map((a) => ({ ...a }));
    } else {
      const list = prev[blockId] || [];
      let nextList: Array<{ month: number; method: string }>;
      if (action === "add") {
        if (list.some((a) => a.month === month)) return;
        const bi = blockInfo.find((b) => b.block_id === blockId);
        const defaultMethod = bi?.accepted_methods[0] || "broadcast";
        nextList = [...list, { month, method: defaultMethod }];
      } else {
        if (!list.some((a) => a.month === month)) return;
        nextList = list.filter((a) => a.month !== month);
      }
      updated = { ...prev, [blockId]: nextList };
    }
    liveAppsRef.current = updated;
    setAppsByBlock(updated);
    emitChange(updated);
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
                Schedule applies to all {blockInfo.length} blocks in this programme — timing is
                agronomy-driven and independent of how blocks are grouped upstairs.
                Turn off if a specific block needs different months or methods.
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

              <MonthRows
                apps={sharedApps}
                availableMethods={sharedMethods}
                onMonthChange={(idx, month) => updateSharedApplication(idx, "month", month)}
                onToggleMethod={(month, method) => {
                  // Find existing entry for this (month, method) — if present, remove; else add.
                  const idx = sharedApps.findIndex((a) => a.month === month && a.method === method);
                  if (idx >= 0) {
                    removeSharedApplication(idx);
                  } else {
                    broadcastApps([...sharedApps, { month, method }]);
                  }
                }}
                onRemoveMonth={(month) => {
                  // Drop ALL methods scheduled in that month
                  broadcastApps(sharedApps.filter((a) => a.month !== month));
                }}
              />

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
          <div
            key={bi.block_id}
            className={`rounded-xl border bg-white ${bi.inherited_from_group ? "border-dashed bg-amber-50/40" : ""}`}
          >
            {/* Block header */}
            <div className="flex items-center justify-between border-b px-4 py-3">
              <div className="flex items-center gap-2">
                <div>
                  <p className="font-semibold text-[var(--sapling-dark)]">
                    {bi.block_name}
                    {typeof bi.block_area_ha === "number" && (
                      <span className="ml-2 text-xs font-normal text-muted-foreground">
                        {bi.block_area_ha} ha
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">{bi.crop}</p>
                </div>
                {bi.inherited_from_group && (
                  <span className="ml-1 rounded-full border border-amber-300 bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-800">
                    Follows Group {bi.inherited_from_group}
                  </span>
                )}
              </div>
              {bi.crop_type !== "perennial" && !bi.inherited_from_group && (
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

            {bi.inherited_from_group && (
              <p className="border-b px-4 py-2 text-[11px] text-amber-800">
                No soil analysis — this block rides Group {bi.inherited_from_group}&rsquo;s plan
                {bi.inherited_from_block_name ? ` (driven by ${bi.inherited_from_block_name})` : ""}.
                Per-ha rates apply to its area; growth stages and schedule are read-only.
              </p>
            )}

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

            {/* Growth stage timeline. Rotate the month sequence so the
                bar starts at the planting month — for SH crops planted
                in Oct, a Jan-Dec layout reads as discontinuous (mid-
                cycle on the left, planting on the right). Starting at
                planting month gives a clean left→right growth cycle.
                Cells are click + drag-paint to schedule applications. */}
            <div className="px-4 py-3">
              <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Growth Stages
                <span className="ml-2 normal-case text-muted-foreground/70">
                  {bi.inherited_from_group
                    ? "· read-only for inherited blocks"
                    : "· cycle starts at planting month · click or drag months to schedule"}
                </span>
              </p>
              <GrowthStageStrip
                plantMonth={plantMonth}
                shiftedStages={shiftedStages}
                appMonths={new Set(blockApps.map((a) => a.month))}
                onPaint={(month, action) => paintMonth(bi.block_id, month, action)}
                readOnly={!!bi.inherited_from_group}
              />
            </div>

            {/* Applications — hidden when the shared-schedule panel
                above is driving every block, and hidden for inherited
                passengers (their schedule rides the group's mate). */}
            {!sharedSchedule && !bi.inherited_from_group && (
              <div className="border-t px-4 py-3 space-y-2">
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Fertilizer Applications ({blockApps.length})
                </p>

                {blockApps.length === 0 && (
                  <p className="py-2 text-center text-xs text-muted-foreground">No applications added yet</p>
                )}

                <MonthRows
                  apps={blockApps}
                  availableMethods={bi.accepted_methods}
                  stageForMonth={(m) => getStageForMonth(m, shiftedStages)}
                  onMonthChange={(idx, month) => updateApplication(bi.block_id, idx, "month", month)}
                  onToggleMethod={(month, method) => {
                    const idx = blockApps.findIndex((a) => a.month === month && a.method === method);
                    if (idx >= 0) {
                      removeApplication(bi.block_id, idx);
                    } else {
                      const updated = {
                        ...appsByBlock,
                        [bi.block_id]: [...blockApps, { month, method }],
                      };
                      setAppsByBlock(updated);
                      emitChange(updated);
                    }
                  }}
                  onRemoveMonth={(month) => {
                    const updated = {
                      ...appsByBlock,
                      [bi.block_id]: blockApps.filter((a) => a.month !== month),
                    };
                    setAppsByBlock(updated);
                    emitChange(updated);
                  }}
                />

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

// ─────────────────────────────────────────────────────────────────────
// MonthRows — chip-toggle multi-select per month
// ─────────────────────────────────────────────────────────────────────
//
// Replaces the per-application Month + Method dropdown pair with one
// row per month, holding chips for each method available on the field.
// Click a chip to toggle that (month, method) on or off. Lets the
// agronomist stack a Broadcast + Fertigation pass on the same month
// (paired-application case) without adding two rows.

interface MonthRowsProps {
  apps: Array<{ month: number; method: string }>;
  availableMethods: string[];
  stageForMonth?: (month: number) => GrowthStage | null | undefined;
  onMonthChange: (idx: number, month: number) => void;
  onToggleMethod: (month: number, method: string) => void;
  onRemoveMonth: (month: number) => void;
}

function MonthRows({
  apps,
  availableMethods,
  stageForMonth,
  onMonthChange,
  onToggleMethod,
  onRemoveMonth,
}: MonthRowsProps) {
  // Per-row "advanced" toggle — chips stay collapsed by default since the
  // field's accepted_methods already declared capability at block setup.
  // Field infrastructure rarely changes, so the default method is right
  // for almost every application; the override is for the paired-method
  // edge case (broadcast + foliar in the same month, etc).
  const [overrideOpen, setOverrideOpen] = useState<Set<number>>(new Set());
  const toggleOverride = (month: number) =>
    setOverrideOpen((prev) => {
      const next = new Set(prev);
      if (next.has(month)) next.delete(month);
      else next.add(month);
      return next;
    });

  // Group apps by month so each month renders one row regardless of how
  // many methods are stacked on it.
  const byMonth = new Map<number, string[]>();
  for (const a of apps) {
    if (!byMonth.has(a.month)) byMonth.set(a.month, []);
    byMonth.get(a.month)!.push(a.method);
  }
  // Render in season order
  const months = Array.from(byMonth.keys()).sort(
    (a, b) => seasonOrderIndex(a, SEASON_ANCHOR) - seasonOrderIndex(b, SEASON_ANCHOR),
  );

  // Hide the override affordance entirely when there's no choice to make.
  const hasAlternatives = availableMethods.length > 1;

  return (
    <div className="space-y-2">
      {months.map((month) => {
        const selected = new Set(byMonth.get(month) || []);
        const stage = stageForMonth?.(month);
        // Find the LAST app idx in original `apps` for this month — used
        // by the month-change handler to relabel the entire month group.
        const groupAppIndices = apps
          .map((a, i) => (a.month === month ? i : -1))
          .filter((i) => i >= 0);
        const isOverride = overrideOpen.has(month);
        const selectedList = Array.from(selected);
        return (
          <div
            key={month}
            className="flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2"
          >
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              Month
              <select
                value={month}
                onChange={(e) => {
                  // Re-target every entry for this month to the new month.
                  const newMonth = parseInt(e.target.value);
                  for (const idx of groupAppIndices) {
                    onMonthChange(idx, newMonth);
                  }
                }}
                className="rounded border bg-white px-2 py-1 text-sm font-medium text-[var(--sapling-dark)]"
              >
                {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => (
                  <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                ))}
              </select>
            </label>

            {/* Selected method(s) as compact badges. The default already
                came from the field's accepted_methods, so most rows will
                show one badge and never need the override. */}
            <div className="flex flex-wrap gap-1">
              {selectedList.map((m) => (
                <span
                  key={m}
                  className="rounded-full bg-orange-50 px-2 py-0.5 text-[11px] font-medium text-[var(--sapling-orange)]"
                >
                  {methodLabel(m)}
                </span>
              ))}
            </div>

            {hasAlternatives && (
              <button
                type="button"
                onClick={() => toggleOverride(month)}
                className="text-[11px] font-medium text-[var(--sapling-medium-grey)] underline-offset-2 hover:text-[var(--sapling-dark)] hover:underline"
              >
                {isOverride ? "Hide methods" : "Override method"}
              </button>
            )}

            {stage && (
              <span className="text-xs text-muted-foreground">{stage.stage_name}</span>
            )}
            <button
              onClick={() => onRemoveMonth(month)}
              aria-label="Remove month"
              className="ml-auto rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
            >
              <X className="size-3.5" />
            </button>

            {/* Advanced — full chip strip. Shown only when the user opts
                into overriding the default for this row. */}
            {hasAlternatives && isOverride && (
              <div className="basis-full pt-1">
                <p className="mb-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                  Methods (click to toggle)
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {availableMethods.map((m) => {
                    const isOn = selected.has(m);
                    return (
                      <button
                        key={m}
                        type="button"
                        onClick={() => onToggleMethod(month, m)}
                        className={`rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ${
                          isOn
                            ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                            : "border-gray-200 text-gray-500 hover:border-gray-400"
                        }`}
                      >
                        {methodLabel(m)}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// GrowthStageStrip — click + drag to schedule applications
// ─────────────────────────────────────────────────────────────────────
//
// One row per month coloured by growth stage, with a stage-name overlay
// underneath. Pointer-down on a cell starts a paint gesture: if the cell
// already has an application the gesture removes; otherwise it adds.
// Pointer-enter on subsequent cells (with the button still held) extends
// the same action across the range. Pointer-up anywhere ends the gesture.
//
// Touch users get tap-to-toggle via pointerdown; multi-cell drag on touch
// would need elementFromPoint plumbing, which we skip for v1 — the
// agronomist's primary surface is desktop.

interface GrowthStageStripProps {
  plantMonth: number;
  shiftedStages: GrowthStage[];
  appMonths: Set<number>;
  onPaint: (month: number, action: "add" | "remove") => void;
  /** Inherited blocks ride a group's plan — show the stages but block
   * paint gestures so the user can't accidentally author a schedule
   * that nothing will apply. */
  readOnly?: boolean;
}

function GrowthStageStrip({
  plantMonth,
  shiftedStages,
  appMonths,
  onPaint,
  readOnly = false,
}: GrowthStageStripProps) {
  const [paintAction, setPaintAction] = useState<null | "add" | "remove">(null);
  // Months already painted in the current gesture so re-entering a cell
  // (e.g. dragging back) doesn't ping-pong its state.
  const visitedRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    const stop = () => {
      setPaintAction(null);
      visitedRef.current.clear();
    };
    window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", stop);
    return () => {
      window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", stop);
    };
  }, []);

  const monthSequence: number[] = [];
  for (let i = 0; i < 12; i++) {
    monthSequence.push(((plantMonth - 1 + i) % 12) + 1);
  }

  const startPaint = (m: number) => {
    const action: "add" | "remove" = appMonths.has(m) ? "remove" : "add";
    setPaintAction(action);
    visitedRef.current = new Set([m]);
    onPaint(m, action);
  };

  const continuePaint = (m: number) => {
    if (!paintAction) return;
    if (visitedRef.current.has(m)) return;
    visitedRef.current.add(m);
    onPaint(m, paintAction);
  };

  return (
    <>
      <div className="flex select-none gap-0.5 overflow-hidden rounded-lg">
        {monthSequence.map((m) => {
          const stage = getStageForMonth(m, shiftedStages);
          const stageIdx = stage ? shiftedStages.indexOf(stage) : -1;
          const colorClass = stageIdx >= 0
            ? STAGE_COLORS[stageIdx % STAGE_COLORS.length]
            : "bg-gray-100 text-gray-400";
          const hasApp = appMonths.has(m);
          const isPlanting = m === plantMonth;

          return (
            <div
              key={m}
              role={readOnly ? undefined : "button"}
              aria-pressed={readOnly ? undefined : hasApp}
              aria-label={`${MONTH_NAMES[m]} — ${stage?.stage_name || "no stage"}${hasApp ? " (scheduled)" : ""}`}
              tabIndex={readOnly ? undefined : 0}
              onPointerDown={readOnly ? undefined : (e) => {
                // Prevent the browser from capturing the pointer to the
                // first cell (which would block pointerenter on neighbours).
                e.preventDefault();
                (e.currentTarget as HTMLElement).releasePointerCapture?.(e.pointerId);
                startPaint(m);
              }}
              onPointerEnter={readOnly ? undefined : (e) => {
                if (e.buttons > 0) continuePaint(m);
              }}
              onKeyDown={readOnly ? undefined : (e) => {
                if (e.key === " " || e.key === "Enter") {
                  e.preventDefault();
                  onPaint(m, appMonths.has(m) ? "remove" : "add");
                }
              }}
              className={`flex-1 py-1.5 text-center text-[10px] font-medium transition-shadow ${colorClass} ${
                readOnly ? "cursor-default opacity-80" : "cursor-pointer"
              } ${
                hasApp
                  ? "ring-2 ring-inset ring-[var(--sapling-orange)]"
                  : readOnly
                    ? ""
                    : "ring-1 ring-inset ring-transparent hover:ring-gray-400"
              } ${isPlanting ? "border-b-2 border-black" : ""}`}
              title={
                readOnly
                  ? stage?.stage_name || "No stage"
                  : `${stage?.stage_name || "No stage"} — ${hasApp ? "click to remove" : "click to schedule"}`
              }
            >
              {MONTH_NAMES[m]?.slice(0, 3)}
            </div>
          );
        })}
      </div>
      {/* Stage names aligned under their months */}
      <div className="pointer-events-none relative mt-0.5 flex gap-0.5">
        {(() => {
          // Build spans: walk the rotated monthSequence and group adjacent
          // months that share the same stage.
          const cells: Array<{
            stage: GrowthStage;
            stageIdx: number;
            startCol: number;
            span: number;
          }> = [];
          let prevStageIdx = -1;
          let currentStart = 0;
          let currentSpan = 0;

          for (let i = 0; i < 12; i++) {
            const m = monthSequence[i];
            const stage = getStageForMonth(m, shiftedStages);
            const idx = stage ? shiftedStages.indexOf(stage) : -1;
            if (idx !== prevStageIdx) {
              if (prevStageIdx >= 0 && currentSpan > 0) {
                cells.push({
                  stage: shiftedStages[prevStageIdx],
                  stageIdx: prevStageIdx,
                  startCol: currentStart,
                  span: currentSpan,
                });
              }
              currentStart = i;
              currentSpan = idx >= 0 ? 1 : 0;
              prevStageIdx = idx;
            } else if (idx >= 0) {
              currentSpan++;
            }
          }
          if (prevStageIdx >= 0 && currentSpan > 0) {
            cells.push({
              stage: shiftedStages[prevStageIdx],
              stageIdx: prevStageIdx,
              startCol: currentStart,
              span: currentSpan,
            });
          }

          return cells.map((c) => {
            const [bg, fg] = STAGE_COLORS[c.stageIdx % STAGE_COLORS.length].split(" ");
            return (
              <div
                key={`${c.stage.stage_name}-${c.startCol}`}
                className={`overflow-hidden rounded-sm py-0.5 text-center text-[9px] font-medium leading-tight ${bg} ${fg}`}
                style={{
                  position: "absolute",
                  left: `${(c.startCol / 12) * 100}%`,
                  width: `${(c.span / 12) * 100}%`,
                }}
                title={c.stage.stage_name}
              >
                {c.stage.stage_name}
              </div>
            );
          });
        })()}
        {/* Spacer for height */}
        <div className="h-4 w-full" />
      </div>
    </>
  );
}
