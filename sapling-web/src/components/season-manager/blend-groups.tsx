"use client";

/**
 * Wizard Step 3 — agronomist's review of the engine's programme before
 * approving the artifact. Same visual language as the saved-artifact
 * view (`GroupBlendTimeline.tsx`): per-group timeline, A1/A2/A3 codes
 * within Group A, B1/B2 within Group B, etc., one-line "why this
 * blend" briefs, nutrient chips per row.
 *
 * This step is admin-shaped — it shows raw-material audit (collapsed)
 * for QA, which the client-facing artifact view does NOT.
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";
import { MONTH_NAMES, methodLabel, seasonOrderIndex } from "@/lib/season-constants";

const SEASON_ANCHOR = new Date().getMonth() + 1;

// ── Types ───────────────────────────────────────────────────────────

export interface ApplicationBlendData {
  stage_name: string;
  month: number;
  method: string;
  sa_notation: string;
  rate_kg_ha: number;
  events_count: number;
  dates_label?: string;
  cost_per_ton?: number;
  exact?: boolean;
  nutrients_per_ha?: Record<string, number>;
  recipe?: Array<{ material: string; type: string; kg: number; pct: number; cost: number }>;
  is_foliar?: boolean;
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

// ── Constants ───────────────────────────────────────────────────────

const NPK_KEYS = ["N", "P2O5", "K2O"] as const;
const SECONDARY_KEYS = ["Ca", "Mg", "S"] as const;
const MICRO_KEYS = ["Zn", "B", "Mn", "Fe", "Cu", "Mo"] as const;

// User-facing labels follow SA grower convention: ratios read as
// N : P : K with the implicit understanding that P / K are oxide forms
// (P₂O₅, K₂O). Engine internals keep the explicit `P2O5` / `K2O` keys
// to preserve chemistry; this map is the display boundary.
const NUTRIENT_LABEL: Record<string, string> = {
  N: "N", P2O5: "P", K2O: "K",
  Ca: "Ca", Mg: "Mg", S: "S",
  Zn: "Zn", B: "B", Mn: "Mn", Fe: "Fe", Cu: "Cu", Mo: "Mo",
};

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

// Each method's agronomic role — used by the split-explanation helper
// so we can say "broadcast for soil correction; side-dress for timed N"
// rather than "broadcast vs side-dress" (jargon).
const METHOD_ROLE: Record<string, string> = {
  broadcast:   "soil correction (slow build-up)",
  band:        "root-zone placement",
  side_dress:  "timed availability",
  fertigation: "soluble delivery during irrigation",
  foliar:      "leaf-direct correction",
  soil_basal:  "pre-plant base",
  seed_treat:  "seed-coat protection",
  drench:      "root-zone drench",
};

// ── Number formatting ───────────────────────────────────────────────

function fmtNumber(n: number, dp = 1): string {
  if (n === 0) return "0";
  if (n >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  if (Math.abs(n) >= 100) return n.toFixed(0);
  return n.toFixed(dp);
}

function fmtMicro(kg_per_ha: number): string {
  if (kg_per_ha < 1) return `${(kg_per_ha * 1000).toFixed(0)} g/ha`;
  return `${kg_per_ha.toFixed(2)} kg/ha`;
}

// ── Group lettering ─────────────────────────────────────────────────

function groupLetter(groupId: string): string {
  return groupId.replace(/^cluster_/i, "");
}

function groupLetterAt(group: BlendGroupData, idx: number): string {
  if (group.group.startsWith("cluster_")) return groupLetter(group.group);
  return String.fromCharCode("A".charCodeAt(0) + idx);
}

// ── Brief synthesis ─────────────────────────────────────────────────

/** Human-friendly headline of which nutrients dominate. Returns up to
 *  the top 2 macro nutrients by kg/ha so the brief reads naturally. */
function dominantNutrients(nutrients: Record<string, number>): string[] {
  const entries = Object.entries(nutrients)
    .filter(([k, v]) => v > 0 && (NPK_KEYS as readonly string[]).concat(SECONDARY_KEYS as readonly string[]).includes(k))
    .sort((a, b) => b[1] - a[1]);
  return entries.slice(0, 2).map(([k]) => NUTRIENT_LABEL[k] ?? k);
}

function brief(app: ApplicationBlendData): string {
  if (app.is_foliar) {
    return `Foliar correction during ${app.stage_name || "this stage"} — finalised at quote time.`;
  }
  const top = dominantNutrients(app.nutrients_per_ha || {});
  const stage = app.stage_name || `Stage ${app.month}`;
  const method = methodLabel(app.method).toLowerCase();
  const role = METHOD_ROLE[app.method] ?? "";
  const eventsClause = app.events_count > 1 ? ` Split into ${app.events_count} events.` : "";
  const roleClause = role ? ` — ${role}` : "";
  if (top.length === 0) {
    return `${stage} window via ${method}${roleClause}.${eventsClause}`;
  }
  if (top.length === 1) {
    return `${stage} window targets ${top[0]}; applied as ${method}${roleClause}.${eventsClause}`;
  }
  return `${stage} window targets ${top.join(" + ")}; applied as ${method}${roleClause}.${eventsClause}`;
}

// ── Split-window detection + explanation ────────────────────────────

interface StageBucket {
  stageKey: string;
  stage_name: string;
  month: number;
  apps: ApplicationBlendData[];
}

function bucketByStage(applications: ApplicationBlendData[]): StageBucket[] {
  const map = new Map<string, StageBucket>();
  for (const app of applications) {
    const key = `${app.stage_name || "(unnamed)"}|${app.month}`;
    if (!map.has(key)) {
      map.set(key, {
        stageKey: key,
        stage_name: app.stage_name || "Untitled stage",
        month: app.month,
        apps: [],
      });
    }
    map.get(key)!.apps.push(app);
  }
  return Array.from(map.values()).sort(
    (a, b) =>
      seasonOrderIndex(a.month, SEASON_ANCHOR) - seasonOrderIndex(b.month, SEASON_ANCHOR),
  );
}

/** When a stage produces multiple blends, explain WHY in one line.
 *
 * Three split flavours:
 *   1. Same method × different blends → bag-incompatibility (e.g. urea
 *      + lime → NH₃ loss). The consolidator never merges these so a
 *      same-method pair survives only when chemistry forced it.
 *   2. Different methods → parallel passes; each method serves the
 *      nutrient class it does best (broadcast for soil-corrective Ca,
 *      side-dress for timed N).
 *   3. Foliar + soil → foliar is a leaf-direct supplement layered on
 *      top of the soil programme; never replaces it.
 */
function explainSplit(apps: ApplicationBlendData[]): string {
  if (apps.length < 2) return "";
  const methods = new Set(apps.map((a) => a.method));
  const hasFoliar = apps.some((a) => a.is_foliar);
  const hasSoil = apps.some((a) => !a.is_foliar);

  if (hasFoliar && hasSoil) {
    return "Foliar layered on top of the soil pass — leaf-direct supplement, not a replacement.";
  }

  if (methods.size === 1) {
    return "Products can't share a bag (e.g. urea + lime/SSP → NH₃ loss). Kept as separate batches.";
  }

  // Different methods — describe what each method's blend is doing.
  const parts: string[] = [];
  for (const a of apps) {
    const top = dominantNutrients(a.nutrients_per_ha || {});
    const role = METHOD_ROLE[a.method] ?? methodLabel(a.method).toLowerCase();
    const headline = top.length > 0 ? top.join(" + ") : "supporting nutrients";
    parts.push(`${methodLabel(a.method)} for ${headline} (${role})`);
  }
  return `Parallel passes — ${parts.join("; ")}.`;
}

// ── Components ──────────────────────────────────────────────────────

export function BlendGroups({ blendGroups, isAdmin }: BlendGroupsProps) {
  if (blendGroups.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No programmes generated yet.
      </div>
    );
  }
  const totalEvents = blendGroups.reduce(
    (n, g) => n + g.applications.reduce((m, a) => m + (a.events_count || 1), 0),
    0,
  );
  const totalApps = blendGroups.reduce((n, g) => n + g.applications.length, 0);
  return (
    <div className="space-y-4">
      <header>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">
          Programme · {blendGroups.length} group{blendGroups.length !== 1 ? "s" : ""}
        </h3>
        <p className="text-sm text-muted-foreground">
          {totalApps} application{totalApps !== 1 ? "s" : ""}
          {totalEvents > totalApps && ` · ${totalEvents} events scheduled`} —
          review the schedule below before approving.
        </p>
      </header>
      {blendGroups.map((group, idx) => (
        <GroupCard
          key={group.group}
          group={group}
          letter={groupLetterAt(group, idx)}
          isAdmin={isAdmin}
        />
      ))}
    </div>
  );
}

function GroupCard({
  group,
  letter,
  isAdmin,
}: {
  group: BlendGroupData;
  letter: string;
  isAdmin: boolean;
}) {
  const buckets = bucketByStage(group.applications);
  // Number applications A1, A2, … in season order, regardless of how
  // they cluster into split-windows (paired blends still get
  // sequential codes — the connector visual makes the pairing obvious).
  let counter = 0;
  const numbered: Array<{ code: string; app: ApplicationBlendData }> = [];
  for (const bucket of buckets) {
    for (const app of bucket.apps) {
      counter += 1;
      numbered.push({ code: `${letter}${counter}`, app });
    }
  }
  const codeOf = new Map<ApplicationBlendData, string>(
    numbered.map(({ code, app }) => [app, code]),
  );
  const groupTotalKg = group.applications.reduce(
    (s, a) => s + (a.is_foliar ? 0 : a.rate_kg_ha * (a.events_count || 1) * group.total_area_ha),
    0,
  );
  return (
    <Card>
      <CardContent className="p-5">
        <header className="mb-4 flex flex-wrap items-baseline justify-between gap-2 border-b pb-3">
          <div className="flex items-baseline gap-3">
            <span className="flex size-9 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-base font-bold text-white">
              {letter}
            </span>
            <div>
              <h4 className="text-base font-semibold text-foreground">
                Group {letter}
              </h4>
              <p className="text-xs text-muted-foreground">
                {group.crops.join(", ")}
                {group.block_names.length > 0 && ` · ${group.block_names.join(", ")}`}
                {group.total_area_ha > 0 && ` · ${group.total_area_ha} ha`}
              </p>
            </div>
          </div>
          <span className="rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
            {group.applications.length} application{group.applications.length !== 1 ? "s" : ""}
          </span>
        </header>

        <ol className="space-y-3">
          {buckets.map((bucket) => (
            <StageEntry
              key={bucket.stageKey}
              bucket={bucket}
              codeOf={codeOf}
              area_ha={group.total_area_ha}
            />
          ))}
        </ol>

        <GroupSeasonTotals group={group} />

        <p className="mt-2 text-[11px] text-muted-foreground">
          Estimated product total: <span className="font-medium tabular-nums">{fmtNumber(groupTotalKg, 0)} kg</span>{" "}
          across {group.applications.filter((a) => !a.is_foliar).length} soil application
          {group.applications.filter((a) => !a.is_foliar).length !== 1 ? "s" : ""} —
          actual rate depends on the formulation chosen at quote time.
        </p>

        {isAdmin && group.applications.some((a) => a.recipe && a.recipe.length > 0) && (
          <AdminAuditFold group={group} codeOf={codeOf} />
        )}
      </CardContent>
    </Card>
  );
}

function StageEntry({
  bucket,
  codeOf,
  area_ha,
}: {
  bucket: StageBucket;
  codeOf: Map<ApplicationBlendData, string>;
  area_ha: number;
}) {
  const split = bucket.apps.length > 1;
  const reason = split ? explainSplit(bucket.apps) : "";
  return (
    <li className={split ? "rounded-lg border-l-4 border-[var(--sapling-orange)]/50 bg-orange-50/30 p-3" : ""}>
      {split && (
        <div className="mb-2">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--sapling-orange)]">
            Split window — {MONTH_NAMES[bucket.month]} · {bucket.stage_name}
          </p>
          <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
            {reason}
          </p>
        </div>
      )}
      <div className={split ? "space-y-2" : ""}>
        {bucket.apps.map((app) => (
          <ApplicationRow
            key={codeOf.get(app)!}
            code={codeOf.get(app)!}
            app={app}
            area_ha={area_ha}
            inSplit={split}
          />
        ))}
      </div>
    </li>
  );
}

function ApplicationRow({
  code,
  app,
  area_ha,
  inSplit,
}: {
  code: string;
  app: ApplicationBlendData;
  area_ha: number;
  inSplit: boolean;
}) {
  const nutrients = app.nutrients_per_ha || {};
  const totalKg = app.rate_kg_ha * (app.events_count || 1) * (area_ha || 0);
  const macros = [...NPK_KEYS, ...SECONDARY_KEYS]
    .map((k) => [k, nutrients[k]] as const)
    .filter(([, v]) => v && v > 0);
  const micros = MICRO_KEYS
    .map((k) => [k, nutrients[k]] as const)
    .filter(([, v]) => v && v > 0);
  const methodChip = (
    <span
      className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
        app.is_foliar
          ? "bg-violet-100 text-violet-800"
          : METHOD_CHIP_CLASS[app.method] || "bg-gray-100 text-gray-700"
      }`}
    >
      {methodLabel(app.method)}
    </span>
  );
  return (
    <div className={`grid grid-cols-[auto_1fr] items-start gap-3 ${inSplit ? "rounded-md bg-white p-2.5" : "py-2"}`}>
      <span className="rounded-md bg-[var(--sapling-orange)] px-2 py-1 text-xs font-bold text-white">
        {code}
      </span>
      <div className="min-w-0 space-y-1.5">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
          {!inSplit && (
            <span className="text-sm font-semibold text-foreground">
              {MONTH_NAMES[app.month]} · {app.stage_name || "Untitled stage"}
            </span>
          )}
          {methodChip}
          <span className="ml-auto text-right text-sm font-semibold tabular-nums text-foreground">
            {app.is_foliar
              ? "—"
              : app.method === "fertigation" && app.concentrate_volume_l
                ? `${fmtNumber(app.concentrate_volume_l / (app.events_count || 1) / Math.max(area_ha, 1), 0)} L/ha`
                : app.rate_kg_ha
                  ? `${fmtNumber(app.rate_kg_ha, 0)} kg/ha`
                  : "—"}
            {app.events_count > 1 && (
              <span className="ml-1 text-[10px] font-normal text-muted-foreground">/event</span>
            )}
          </span>
        </div>
        {!app.is_foliar && macros.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {macros.map(([k, v]) => (
              <span
                key={k}
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] tabular-nums"
              >
                <span className="font-semibold">{NUTRIENT_LABEL[k] ?? k}</span>
                <span className="ml-1">{fmtNumber(v as number)}</span>
              </span>
            ))}
            {micros.map(([k, v]) => (
              <span
                key={k}
                className="rounded bg-violet-50 px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-violet-900"
              >
                <span className="font-semibold">{NUTRIENT_LABEL[k] ?? k}</span>
                <span className="ml-1">{fmtMicro(v as number)}</span>
              </span>
            ))}
          </div>
        )}
        <p className="text-[11px] leading-snug text-muted-foreground">
          {brief(app)}
        </p>
        <p className="text-[11px] text-muted-foreground/80">
          {app.events_count > 1 && (
            <>
              {app.events_count} events
              {app.dates_label && ` · ${app.dates_label}`}
              {!app.is_foliar && totalKg > 0 && ` · ${fmtNumber(totalKg, 0)} kg total this stage`}
            </>
          )}
          {app.events_count <= 1 && !app.is_foliar && totalKg > 0 && (
            <>{fmtNumber(totalKg, 0)} kg total ({area_ha} ha)</>
          )}
          {app.exact === false && (
            <span className="ml-2 text-amber-600">· estimated</span>
          )}
        </p>
      </div>
    </div>
  );
}

function GroupSeasonTotals({ group }: { group: BlendGroupData }) {
  const totals: Record<string, number> = {};
  for (const app of group.applications) {
    if (app.is_foliar) continue;
    const events = app.events_count || 1;
    const area = group.total_area_ha || 0;
    for (const [k, v] of Object.entries(app.nutrients_per_ha || {})) {
      totals[k] = (totals[k] || 0) + v * events * area;
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
    <div className="mt-4 rounded-lg border bg-orange-50/40 px-3 py-2">
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--sapling-orange)]">
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
              {NUTRIENT_LABEL[e.key]}{" "}
              {e.kg < 1 ? `${(e.kg * 1000).toFixed(0)} g` : `${e.kg.toFixed(2)} kg`}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function AdminAuditFold({
  group,
  codeOf,
}: {
  group: BlendGroupData;
  codeOf: Map<ApplicationBlendData, string>;
}) {
  const [open, setOpen] = useState(false);
  const withRecipes = group.applications.filter((a) => a.recipe && a.recipe.length > 0);
  if (withRecipes.length === 0) return null;
  return (
    <div className="mt-4 rounded-lg border bg-gray-50/60">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-[11px] font-medium uppercase tracking-wider text-muted-foreground hover:text-foreground"
      >
        {open ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
        Admin audit · raw materials picked by LP
        <span className="ml-auto text-[10px] font-normal normal-case text-muted-foreground">
          actual products may change at quote time
        </span>
      </button>
      {open && (
        <div className="space-y-2 border-t bg-white px-3 py-2">
          {withRecipes.map((app) => (
            <div key={codeOf.get(app)!}>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {codeOf.get(app)!} · {methodLabel(app.method)}
              </p>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-left text-[10px] uppercase tracking-wider text-muted-foreground">
                    <th className="py-1 pr-3 font-medium">Material</th>
                    <th className="py-1 pr-3 font-medium">Type</th>
                    <th className="py-1 pr-3 text-right font-medium">kg</th>
                    <th className="py-1 pr-3 text-right font-medium">%</th>
                  </tr>
                </thead>
                <tbody>
                  {app.recipe!.map((r, ri) => (
                    <tr key={ri} className="border-b border-border/30 last:border-0">
                      <td className="py-1 pr-3">{r.material}</td>
                      <td className="py-1 pr-3 text-muted-foreground">{r.type}</td>
                      <td className="py-1 pr-3 text-right tabular-nums">{r.kg.toFixed(1)}</td>
                      <td className="py-1 pr-3 text-right tabular-nums">{r.pct.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
