"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MONTH_NAMES, methodLabel, seasonOrderIndex } from "@/lib/season-constants";

const SEASON_ANCHOR = new Date().getMonth() + 1;

/** Strip any "cluster_" prefix the engine emits (e.g. cluster_A → A)
 * so the badge / header read as plain group letters. */
function groupLetter(groupId: string): string {
  return groupId.replace(/^cluster_/i, "");
}

/** Singleton groups (one block, no cluster letter) get a positional
 * letter computed from index — "Group B / C / …" reads cleaner than
 * "Group Blok N5 — Young Beaumont/A4" which duplicates the block name
 * already shown in the subtitle. */
function groupLetterAt(group: BlendGroupData, idx: number): string {
  if (group.group.startsWith("cluster_")) return groupLetter(group.group);
  return String.fromCharCode("A".charCodeAt(0) + idx);
}

export interface ApplicationBlendData {
  stage_name: string;
  /** First month the recipe is applied in this stage. */
  month: number;
  method: string;
  sa_notation: string;
  /** Rate per individual event (kg/ha). Multiply by events_count for the
   * per-stage total. Estimated — actual product rate depends on the
   * blend formulation chosen at quote time. */
  rate_kg_ha: number;
  events_count: number;
  dates_label?: string;
  cost_per_ton?: number;
  exact?: boolean;
  /** Nutrients the engine targets to deliver per HA per event (kg).
   * Includes macros (N, P2O5, K2O, Ca, Mg, S) and micros (Zn, B, Mn,
   * Fe, Cu, Mo) when present. Drives the formula display. */
  nutrients_per_ha?: Record<string, number>;
  /** Raw materials chosen by the LP. Admin-only audit data — agronomist
   * UI shows only the formula + nutrients. Materials available at
   * production may be different from these (months apart). */
  recipe?: Array<{ material: string; type: string; kg: number; pct: number; cost: number }>;
  is_foliar?: boolean;
  /** Fertigation only — total stock-tank volume (Part A + Part B
   * combined) across the stage. Drives the L/event display. */
  concentrate_volume_l?: number;
}

export interface BlendGroupData {
  group: string;
  crops: string[];
  block_names: string[];
  total_area_ha: number;
  applications: ApplicationBlendData[];
}

interface BlendGroupsProps {
  blendGroups: BlendGroupData[];
  isAdmin: boolean;
}

export function BlendGroups({ blendGroups, isAdmin }: BlendGroupsProps) {
  if (blendGroups.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No blend groups generated
      </div>
    );
  }

  const totalWindows = blendGroups.reduce((n, g) => n + g.applications.length, 0);
  const totalEvents = blendGroups.reduce(
    (n, g) => n + g.applications.reduce((m, a) => m + (a.events_count || 1), 0),
    0,
  );

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">Optimized Blends</h3>
        <p className="text-sm text-muted-foreground">
          {totalWindows} application window{totalWindows !== 1 ? "s" : ""} across {blendGroups.length} group{blendGroups.length !== 1 ? "s" : ""}
          {totalEvents > totalWindows && <> &middot; {totalEvents} events total</>} —
          each stage-method combination gets its own blend.
        </p>
      </div>

      {blendGroups.map((group, idx) => {
        const letter = groupLetterAt(group, idx);
        const groupEvents = group.applications.reduce((m, a) => m + (a.events_count || 1), 0);
        const groupTotalKg = group.applications.reduce(
          (s, a) => s + (a.is_foliar ? 0 : a.rate_kg_ha * (a.events_count || 1) * group.total_area_ha),
          0,
        );
        return (
          <Card key={group.group} className="overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <span className="flex size-8 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-sm font-bold text-white">
                  {letter}
                </span>
                <div className="flex-1">
                  <CardTitle className="text-base">
                    Group {letter} — {group.applications.length} application window{group.applications.length !== 1 ? "s" : ""}
                    {groupEvents > group.applications.length && (
                      <span className="ml-2 text-xs font-normal text-muted-foreground">
                        ({groupEvents} events)
                      </span>
                    )}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {group.crops.join(", ")} &middot; {group.block_names.join(", ")} &middot; {group.total_area_ha} ha
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {(() => {
                // Group applications by stage so paired passes (e.g.
                // establishment with both a heavy basal Broadcast and a
                // soluble Foliar starter) cluster visually instead of
                // looking like two unrelated "Mar · establishment"
                // cards. Within a stage, sort by method for stable ordering.
                const byStage = new Map<string, ApplicationBlendData[]>();
                for (const app of group.applications) {
                  const key = `${app.stage_name || "(unnamed)"}|${app.month}`;
                  if (!byStage.has(key)) byStage.set(key, []);
                  byStage.get(key)!.push(app);
                }
                const stageEntries = Array.from(byStage.entries()).sort(
                  ([keyA], [keyB]) => {
                    const monthA = parseInt(keyA.split("|")[1], 10);
                    const monthB = parseInt(keyB.split("|")[1], 10);
                    return seasonOrderIndex(monthA, SEASON_ANCHOR) - seasonOrderIndex(monthB, SEASON_ANCHOR);
                  },
                );
                return stageEntries.map(([stageKey, apps]) => {
                  const isPaired = apps.length > 1;
                  const headerApp = apps[0];
                  // When the paired passes all use the SAME method, the
                  // engine kept them separate because of a real chemistry
                  // conflict (e.g. urea + lime/SSP — NH₃ loss). The
                  // within-stage merger collapses everything else, so
                  // anything left as same-method is a genuine block.
                  // Different methods → parallel agronomic strategies
                  // (heavy basal Broadcast + Fertigation starter).
                  const sameMethodSplit = isPaired && apps.every((a) => a.method === apps[0].method);
                  const reasonText = sameMethodSplit
                    ? `${apps.length} passes — kept separate because the products can't share a bag (urea-with-lime or urea-with-SSP would release NH₃).`
                    : `${apps.length} parallel passes via different methods.`;
                  return (
                    <div
                      key={stageKey}
                      className={`rounded-lg border ${isPaired ? "border-[var(--sapling-orange)]/30 bg-orange-50/30" : ""}`}
                    >
                      {isPaired && (
                        <div className="border-b px-3 py-1.5 text-[11px] font-medium text-[var(--sapling-orange)]">
                          {sameMethodSplit ? "Split batches" : "Paired application"} — {MONTH_NAMES[headerApp.month]} · {headerApp.stage_name || "Untitled stage"}
                          <span className="ml-2 font-normal text-muted-foreground">
                            {reasonText}
                          </span>
                        </div>
                      )}
                      {apps.map((app, i) => renderApplicationRow(
                        app, i, isPaired, isAdmin, group.total_area_ha,
                        sameMethodSplit ? `Batch ${i + 1} of ${apps.length}` : undefined,
                      ))}
                    </div>
                  );
                });
              })()}

              {/* Per-group season totals — nutrients delivered + product
                  mass. Programme builder is agronomy-scoped (no cost). */}
              <GroupSeasonTotals group={group} />
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-xs">
                <span className="text-muted-foreground">
                  Estimated product total:
                  {" "}{fmtNumber(groupTotalKg, 0)} kg
                  {" "}across {group.applications.filter((a) => !a.is_foliar).length} application window{group.applications.filter((a) => !a.is_foliar).length !== 1 ? "s" : ""}
                  {" "}— actual rate depends on the formulation chosen at quote time.
                </span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/** Season-total nutrient roll-up per group — sum of (nutrient kg/ha ×
 * events × area_ha) across all applications. The agronomist's "what
 * goes on this farm in total" view. */
function GroupSeasonTotals({ group }: { group: BlendGroupData }) {
  const totals: Record<string, number> = {};
  for (const app of group.applications) {
    if (app.is_foliar) continue;
    const events = app.events_count || 1;
    const area = group.total_area_ha || 0;
    for (const [k, v] of Object.entries(app.nutrients_per_ha || {})) {
      totals[k] = (totals[k] || 0) + (v * events * area);
    }
  }
  const macroEntries = [...NPK_KEYS, ...SECONDARY_KEYS]
    .filter((k) => totals[k] && totals[k] > 0)
    .map((k) => ({ key: k, kg: totals[k] }));
  const microEntries = MICRO_KEYS
    .filter((k) => totals[k] && totals[k] > 0)
    .map((k) => ({ key: k, kg: totals[k] }));
  if (macroEntries.length === 0 && microEntries.length === 0) return null;
  return (
    <div className="rounded-lg border bg-orange-50/30 px-3 py-2">
      <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-[var(--sapling-orange)]">
        Season totals (this group, all blocks)
      </p>
      <div className="grid grid-cols-3 gap-x-4 gap-y-0.5 text-xs sm:grid-cols-6">
        {macroEntries.map((e) => (
          <div key={e.key} className="flex items-baseline justify-between">
            <span className="text-muted-foreground">{NUTRIENT_LABEL[e.key]}</span>
            <span className="font-medium tabular-nums">{fmtNumber(e.kg, 0)} kg</span>
          </div>
        ))}
      </div>
      {microEntries.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 border-t pt-1 text-[11px] text-muted-foreground">
          <span className="font-medium uppercase tracking-wider">micros total:</span>
          {microEntries.map((e) => (
            <span key={e.key}>
              {NUTRIENT_LABEL[e.key]} {e.kg < 1 ? `${(e.kg * 1000).toFixed(0)} g` : `${e.kg.toFixed(2)} kg`}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── SA notation helpers ─────────────────────────────────────────────

/** Macros that participate in the X:Y:Z (W) ratio. */
const NPK_KEYS = ["N", "P2O5", "K2O"] as const;
/** Secondaries shown as appended "Ca x.x%" tokens. */
const SECONDARY_KEYS = ["Ca", "Mg", "S"] as const;
/** Micros — surfaced separately in the nutrients table when present
 * (g/ha or kg/ha depending on size). */
const MICRO_KEYS = ["Zn", "B", "Mn", "Fe", "Cu", "Mo"] as const;
/** Pretty-print names with subscripts. */
const NUTRIENT_LABEL: Record<string, string> = {
  N: "N", P2O5: "P₂O₅", K2O: "K₂O",
  Ca: "Ca", Mg: "Mg", S: "S",
  Zn: "Zn", B: "B", Mn: "Mn", Fe: "Fe", Cu: "Cu", Mo: "Mo",
};

/** Compute SA notation "X:Y:Z (W) + Ca x.x% + Mg y.y% + S z.z%" from
 * the per-event nutrient kg/ha and the total product mass kg/ha. The
 * (W) is the actual NPK-percent of the formulated product; X:Y:Z is
 * the integer ratio scaled so the largest of the three is 15
 * (matches SA grower convention — e.g. 15:1:5 rather than 15.2:0.8:5.0). */
function computeSANotation(nutrients: Record<string, number>, totalMassKgPerHa: number): string {
  if (!totalMassKgPerHa || totalMassKgPerHa <= 0) return "";
  const n = nutrients.N || 0;
  const p = nutrients.P2O5 || 0;
  const k = nutrients.K2O || 0;
  const totalNPK = n + p + k;
  if (totalNPK <= 0) return "";

  const nPct = (n / totalMassKgPerHa) * 100;
  const pPct = (p / totalMassKgPerHa) * 100;
  const kPct = (k / totalMassKgPerHa) * 100;
  const sumPct = nPct + pPct + kPct;
  const peak = Math.max(nPct, pPct, kPct);
  const scale = peak > 0 ? 15 / peak : 0;
  const r = (v: number) => Math.max(0, Math.round(v * scale));
  const s = `${r(nPct)}:${r(pPct)}:${r(kPct)} (${sumPct.toFixed(0)})`;

  const tail: string[] = [];
  for (const key of SECONDARY_KEYS) {
    const v = nutrients[key];
    if (v && v > 0) {
      const pct = (v / totalMassKgPerHa) * 100;
      if (pct >= 0.1) tail.push(`${NUTRIENT_LABEL[key]} ${pct.toFixed(1)}%`);
    }
  }
  return tail.length > 0 ? `${s} + ${tail.join(" + ")}` : s;
}

function microsForRow(nutrients: Record<string, number>): Array<{ key: string; kg_per_ha: number }> {
  return MICRO_KEYS
    .filter((k) => nutrients[k] && nutrients[k] > 0)
    .map((k) => ({ key: k, kg_per_ha: nutrients[k] }));
}

function fmtNumber(n: number, dp = 1): string {
  if (n === 0) return "0";
  if (n >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return n.toFixed(dp);
}

/** Format a micro nutrient — g/ha when small, kg/ha otherwise. */
function fmtMicro(kg_per_ha: number): string {
  if (kg_per_ha < 1) return `${(kg_per_ha * 1000).toFixed(0)} g/ha`;
  return `${kg_per_ha.toFixed(2)} kg/ha`;
}

const METHOD_CHIP_CLASS: Record<string, string> = {
  broadcast:   "bg-amber-100 text-amber-900",
  band:        "bg-orange-100 text-orange-900",
  side_dress:  "bg-yellow-100 text-yellow-900",
  fertigation: "bg-blue-100 text-blue-900",
  foliar:      "bg-violet-100 text-violet-900",
  soil_basal:  "bg-emerald-100 text-emerald-900",
  seed_treat:  "bg-rose-100 text-rose-900",
  drench:      "bg-cyan-100 text-cyan-900",
};

/** One application row. Surfaces formula + rate + per-application total
 * + macros table. Raw materials hidden (not the deliverable at this stage —
 * actual products chosen at quote time). */
function renderApplicationRow(
  app: ApplicationBlendData,
  i: number,
  isPaired: boolean,
  isAdmin: boolean,
  area_ha: number,
  batchLabel?: string,
) {
  const nutrients = app.nutrients_per_ha || {};
  const formula = computeSANotation(nutrients, app.rate_kg_ha) || app.sa_notation || "(no formula)";
  const totalKgPerApp = app.rate_kg_ha * (app.events_count || 1) * (area_ha || 0);
  const micros = microsForRow(nutrients);

  const methodChip = (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
        app.is_foliar
          ? "bg-violet-100 text-violet-800"
          : METHOD_CHIP_CLASS[app.method] || "bg-gray-100 text-gray-700"
      }`}
    >
      {methodLabel(app.method)}
    </span>
  );

  return (
    <div
      key={i}
      className={`${i > 0 ? "border-t" : ""} ${app.is_foliar ? "bg-violet-50/30" : "bg-white"}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 px-3 py-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {!isPaired && (
              <span className="text-sm font-medium text-[var(--sapling-dark)]">
                {MONTH_NAMES[app.month]} &middot; {app.stage_name || "Untitled stage"}
              </span>
            )}
            {methodChip}
            {batchLabel && (
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                · {batchLabel}
              </span>
            )}
          </div>
          {!app.is_foliar && (
            <p className="mt-1 font-mono text-xs text-[var(--sapling-dark)]">
              {formula}
            </p>
          )}
          {app.is_foliar && (
            <p className="mt-1 text-xs text-muted-foreground">
              Foliar — product specified at quote time.
            </p>
          )}
          {!app.is_foliar && app.events_count > 1 && (
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {app.events_count} events{app.dates_label ? <> &middot; {app.dates_label}</> : null}
            </p>
          )}
        </div>
        <div className="text-right">
          {app.is_foliar ? (
            <span className="inline-flex items-center rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-800">
              configure separately
            </span>
          ) : (
            <>
              {app.method === "fertigation" && app.concentrate_volume_l ? (
                <>
                  <p className="text-sm font-bold text-[var(--sapling-dark)]">
                    {fmtNumber(app.concentrate_volume_l / (app.events_count || 1) / (area_ha || 1), 0)} L/ha
                    {app.events_count > 1 && (
                      <span className="text-xs font-normal text-muted-foreground"> /event</span>
                    )}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {fmtNumber(app.rate_kg_ha, 1)} kg/ha solute /event
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {fmtNumber(app.concentrate_volume_l, 0)} L stock-tank total
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm font-bold text-[var(--sapling-dark)]">
                    {app.rate_kg_ha ? `${fmtNumber(app.rate_kg_ha, 0)} kg/ha` : "—"}
                    {app.events_count > 1 && (
                      <span className="text-xs font-normal text-muted-foreground"> /event</span>
                    )}
                  </p>
                  {totalKgPerApp > 0 && (
                    <p className="text-[11px] text-muted-foreground">
                      {fmtNumber(totalKgPerApp)} kg total
                    </p>
                  )}
                </>
              )}
              {app.exact === false && (
                <p className="text-[10px] text-amber-600">Estimated rate</p>
              )}
            </>
          )}
        </div>
      </div>

      {/* Per-event nutrient table — the actual deliverable. Hidden for
          foliar (which is configured separately) and when nutrient data
          isn't carried (e.g. legacy artifacts). */}
      {!app.is_foliar && Object.keys(nutrients).length > 0 && (
        <div className="border-t bg-gray-50/50 px-3 py-2">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Nutrients delivered per ha · per event
          </p>
          <div className="grid grid-cols-3 gap-x-4 gap-y-0.5 text-xs sm:grid-cols-6">
            {[...NPK_KEYS, ...SECONDARY_KEYS].map((key) => {
              const val = nutrients[key];
              if (!val || val <= 0) return null;
              return (
                <div key={key} className="flex items-baseline justify-between">
                  <span className="text-muted-foreground">{NUTRIENT_LABEL[key]}</span>
                  <span className="font-medium tabular-nums">{fmtNumber(val)} kg</span>
                </div>
              );
            })}
          </div>
          {micros.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 border-t pt-1 text-[11px] text-muted-foreground">
              <span className="font-medium uppercase tracking-wider">micros:</span>
              {micros.map((m) => (
                <span key={m.key}>
                  {NUTRIENT_LABEL[m.key]} {fmtMicro(m.kg_per_ha)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Admin-only audit drawer — raw materials the LP picked. NOT
          shown to agronomists; actual products at production may be
          different (months apart). */}
      {app.recipe && app.recipe.length > 0 && isAdmin && !app.is_foliar && (
        <details className="border-t bg-gray-50">
          <summary className="cursor-pointer px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground hover:text-foreground">
            Audit · raw materials picked by LP (admin)
          </summary>
          <div className="overflow-x-auto border-t">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b bg-white text-left">
                  <th className="px-2 py-1.5 font-medium">Material</th>
                  <th className="px-2 py-1.5 font-medium">Type</th>
                  <th className="px-2 py-1.5 text-right font-medium">kg</th>
                  <th className="px-2 py-1.5 text-right font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {app.recipe.map((r, ri) => (
                  <tr key={ri} className="border-b last:border-0">
                    <td className="px-2 py-1">{r.material}</td>
                    <td className="px-2 py-1 text-muted-foreground">{r.type}</td>
                    <td className="px-2 py-1 text-right tabular-nums">{r.kg.toFixed(1)}</td>
                    <td className="px-2 py-1 text-right tabular-nums">{r.pct.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
