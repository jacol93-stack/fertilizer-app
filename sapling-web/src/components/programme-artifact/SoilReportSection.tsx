"use client";

/**
 * Per-block soil analysis visualisation. One panel per real-data block,
 * showing nutrients vs ideal as horizontal range bars + ratios as
 * coloured status pills, both driven by data the engine already
 * produced (factor_findings, nutrient_status, computed_ratios).
 *
 * Dataless blocks (parameters empty / no nutrient_status) are filtered
 * upstream — they ride a group's recipe and have no analysis to show.
 */

import type {
  FactorFinding,
  NutrientStatus,
  SoilSnapshot,
} from "@/lib/types/programme-artifact";
import { FlaskConical } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const STATUS_PALETTE: Record<string, {
  bar: string;
  marker: string;
  pill: string;
  label: string;
}> = {
  low: {
    bar: "bg-amber-200",
    marker: "bg-amber-600",
    pill: "bg-amber-100 text-amber-800 border-amber-300",
    label: "Below optimal",
  },
  ok: {
    bar: "bg-emerald-200",
    marker: "bg-emerald-700",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-300",
    label: "In range",
  },
  high: {
    bar: "bg-rose-200",
    marker: "bg-rose-600",
    pill: "bg-rose-100 text-rose-800 border-rose-300",
    label: "Above optimal",
  },
};

const SEVERITY_PALETTE: Record<string, string> = {
  info: "bg-slate-100 text-slate-700 border-slate-300",
  watch: "bg-amber-50 text-amber-800 border-amber-300",
  warn: "bg-amber-100 text-amber-900 border-amber-400",
  critical: "bg-rose-100 text-rose-900 border-rose-400",
};

const SEVERITY_RANK: Record<string, number> = {
  info: 0,
  watch: 1,
  warn: 2,
  critical: 3,
};

/** Display labels for ratios + computed metrics surfaced via
 * `computed_ratios`. Anything not in this map renders with the raw key. */
const RATIO_LABELS: Record<string, string> = {
  "Ca:Mg": "Ca : Mg",
  "(Ca+Mg):K": "(Ca+Mg) : K",
  "Ca:K": "Ca : K",
  "Mg:K": "Mg : K",
  "K:Mg": "K : Mg",
  "K:Na": "K : Na",
  "P:Zn": "P : Zn",
  "Ca:B": "Ca : B",
  "C:N": "C : N",
  "Al_saturation_pct": "Al saturation",
  "soil_ESP_pct": "Exchangeable Na (ESP)",
  "SAR": "SAR",
  "water_SAR": "Irrigation SAR",
  "water_RSC_meq": "Irrigation RSC",
};

function fmtNumber(n: number): string {
  if (Math.abs(n) >= 100) return n.toFixed(0);
  if (Math.abs(n) >= 10) return n.toFixed(1);
  return n.toFixed(2);
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.min(Math.max(n, lo), hi);
}

/** Single parameter row: label, value, range bar, optimal-band badge. */
function NutrientRangeBar({ row }: { row: NutrientStatus }) {
  const palette = STATUS_PALETTE[row.status] ?? STATUS_PALETTE.ok;
  const cmin = row.chart_min ?? Math.max(0, row.optimal_low * 0.5);
  const cmaxRaw = row.chart_max ?? row.optimal_high * 1.5;
  const cmax = cmaxRaw > cmin ? cmaxRaw : cmin + 1;
  const span = cmax - cmin;
  const pctOf = (v: number) => clamp(((v - cmin) / span) * 100, 0, 100);
  const optStartPct = pctOf(row.optimal_low);
  const optEndPct = pctOf(row.optimal_high);
  const valuePct = pctOf(row.value);

  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium text-foreground/80">
          {row.nutrient_label}
        </span>
        <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${palette.pill}`}>
          {palette.label}
        </span>
      </div>
      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="text-base font-semibold tabular-nums text-foreground">
          {fmtNumber(row.value)}
        </span>
        {row.unit && (
          <span className="text-[11px] text-muted-foreground">{row.unit}</span>
        )}
        <span className="ml-auto text-[11px] text-muted-foreground">
          ideal {fmtNumber(row.optimal_low)}–{fmtNumber(row.optimal_high)}
          {row.unit && ` ${row.unit}`}
        </span>
      </div>
      <div
        className="relative mt-2 h-2 rounded-full bg-muted"
        role="img"
        aria-label={`${row.nutrient_label}: ${row.value}${row.unit ? ` ${row.unit}` : ""}, ideal ${row.optimal_low}–${row.optimal_high}, status ${row.status}`}
      >
        {/* Optimal band */}
        <div
          className="absolute inset-y-0 rounded-full bg-emerald-200/80"
          style={{
            left: `${optStartPct}%`,
            width: `${Math.max(optEndPct - optStartPct, 1.5)}%`,
          }}
        />
        {/* Value marker */}
        <div
          className={`absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow ${palette.marker}`}
          style={{ left: `${valuePct}%` }}
        />
      </div>
    </div>
  );
}

/** One ratio finding rendered as a coloured pill — value, ideal context,
 * and the engine's verdict in plain English. */
function RatioStatusPill({ finding }: { finding: FactorFinding }) {
  const palette = SEVERITY_PALETTE[finding.severity] ?? SEVERITY_PALETTE.info;
  const label = RATIO_LABELS[finding.parameter] ?? finding.parameter;
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${palette}`}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-semibold uppercase tracking-wide">{label}</span>
        <span className="font-mono text-[13px] tabular-nums">
          {fmtNumber(finding.value)}
          {finding.threshold != null && (
            <span className="ml-1 text-[10px] font-normal opacity-70">
              vs {fmtNumber(finding.threshold)}
            </span>
          )}
        </span>
      </div>
      <p className="mt-0.5 text-[11px] leading-snug">{finding.message}</p>
      {finding.recommended_action && (
        <p className="mt-1 text-[10px] italic opacity-80">
          {finding.recommended_action}
        </p>
      )}
    </div>
  );
}

/** Pull together the ratio-shaped findings (kind ∈ antagonism, balance,
 * toxicity, deficiency) and computed_ratios with no matching finding so
 * the user sees both 'numbers in range' and 'numbers flagged'. */
function buildRatioRows(snap: SoilSnapshot): FactorFinding[] {
  const findings = (snap.factor_findings ?? []).filter((f) =>
    ["antagonism", "balance", "toxicity"].includes(f.kind),
  );
  const flaggedParams = new Set(findings.map((f) => f.parameter));
  const computed = snap.computed_ratios ?? {};
  // Ratios the engine computed but didn't flag — surface them as
  // info-severity rows so the agronomist sees a complete picture
  // ("Ca:Mg = 4.0, healthy") rather than only the alarms.
  const passive: FactorFinding[] = Object.entries(computed)
    .filter(([k, v]) => !flaggedParams.has(k) && Number.isFinite(v))
    .map(([k, v]) => ({
      kind: "info",
      severity: "info",
      parameter: k,
      value: Number(v),
      threshold: null,
      message: "Within published range — no action needed.",
      recommended_action: null,
    }));
  // Sort: criticals first, then warns, then watches/info, alphabetically
  // within each tier so the same farm reads consistently across builds.
  const all = [...findings, ...passive];
  all.sort((a, b) => {
    const sa = SEVERITY_RANK[b.severity] ?? 0;
    const sb = SEVERITY_RANK[a.severity] ?? 0;
    if (sa !== sb) return sa - sb;
    return (RATIO_LABELS[a.parameter] ?? a.parameter)
      .localeCompare(RATIO_LABELS[b.parameter] ?? b.parameter);
  });
  return all;
}

/** Visual block soil report — one card per snapshot with real data. */
export function SoilReportSection({ snapshots }: { snapshots: SoilSnapshot[] }) {
  // Skip dataless blocks (no parameters captured at all) and synthetic
  // cluster aggregates — the per-block report is the analyst's view,
  // and cluster aggregates are recapped in the group timeline below.
  const blockSnapshots = snapshots.filter(
    (s) =>
      Object.keys(s.parameters || {}).length > 0 &&
      !s.block_id.startsWith("cluster_"),
  );
  if (blockSnapshots.length === 0) return null;

  return (
    <section className="space-y-3">
      <header className="flex items-center gap-2">
        <FlaskConical className="size-4 text-[var(--sapling-orange)]" />
        <h2 className="text-sm font-semibold uppercase tracking-wide">
          Soil analysis · {blockSnapshots.length} block{blockSnapshots.length !== 1 ? "s" : ""}
        </h2>
      </header>
      <div className="space-y-4">
        {blockSnapshots.map((s) => (
          <SoilReportCard key={s.block_id} snapshot={s} />
        ))}
      </div>
    </section>
  );
}

function SoilReportCard({ snapshot: s }: { snapshot: SoilSnapshot }) {
  const nutrientRows = s.nutrient_status ?? [];
  const ratioRows = buildRatioRows(s);
  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b pb-3">
          <div>
            <h3 className="text-base font-semibold text-foreground">
              {s.block_name}
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {s.block_area_ha} ha
              {s.lab_name && <> · {s.lab_name}</>}
              {s.lab_method && <> · {s.lab_method}</>}
              {s.sample_date && <> · sampled {s.sample_date}</>}
            </p>
          </div>
          {s.headline_signals.length > 0 && (
            <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-medium text-amber-900">
              {s.headline_signals.length} headline signal{s.headline_signals.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {nutrientRows.length > 0 && (
          <div>
            <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Nutrients vs ideal
            </h4>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {nutrientRows.map((row) => (
                <NutrientRangeBar key={row.parameter} row={row} />
              ))}
            </div>
          </div>
        )}

        {ratioRows.length > 0 && (
          <div>
            <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Ratios & balance checks
            </h4>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {ratioRows.map((f, i) => (
                <RatioStatusPill key={`${f.parameter}-${i}`} finding={f} />
              ))}
            </div>
          </div>
        )}

        {s.headline_signals.length > 0 && (
          <div className="rounded-lg border-l-4 border-[var(--sapling-orange)] bg-orange-50/60 px-3 py-2">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--sapling-orange)]">
              Headline signals
            </h4>
            <ul className="mt-1 space-y-0.5 text-xs text-foreground">
              {s.headline_signals.map((sig, i) => (
                <li key={i} className="leading-snug">{sig}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
