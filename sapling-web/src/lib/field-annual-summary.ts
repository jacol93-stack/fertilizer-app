/**
 * Build a per-year summary roll-up from the field's history. One card
 * per calendar year showing yield, total nutrient applied, key analyses,
 * and any notable events. Drives the "Annual summary" section on the
 * field dashboard's historical-analysis view.
 */

export interface FieldApplicationRow {
  applied_date: string;
  product_label: string | null;
  rate_kg_ha: number | null;
  rate_l_ha: number | null;
  method: string | null;
  nutrients_kg_per_ha: Record<string, number> | null;
  notes: string | null;
}

export interface FieldEventRow {
  event_date: string;
  event_type: string;
  title: string;
  description: string | null;
}

export interface SoilRow {
  analysis_date?: string | null;
  created_at?: string;
  soil_values?: Record<string, number> | null;
}

export interface LeafRow {
  sample_date?: string | null;
  created_at?: string;
  classifications: Record<string, string> | null;
}

export interface YieldRow {
  season: string;
  yield_actual: number;
  yield_unit: string;
  harvest_date?: string | null;
}

export interface AnnualSummary {
  year: string;
  yieldTotal: number | null;
  yieldUnit: string | null;
  nutrientTotals: Record<string, number>; // kg/ha summed across applications
  applicationCount: number;
  soilSampleCount: number;
  leafSampleCount: number;
  leafLowFlags: string[]; // unique nutrients flagged "low" or "deficient" across leaf analyses this year
  events: FieldEventRow[];
}

function yearOf(iso: string | null | undefined): string | null {
  if (!iso || iso.length < 4) return null;
  return iso.slice(0, 4);
}

function pickYearFromSeason(season: string): string {
  // Season "2026/2027" → "2026"; bare "2026" → "2026"; fallback → ""
  const m = season.match(/^(\d{4})/);
  return m ? m[1] : "";
}

export function buildAnnualSummaries({
  applications,
  events,
  soil,
  leaf,
  yields,
}: {
  applications: FieldApplicationRow[];
  events: FieldEventRow[];
  soil: SoilRow[];
  leaf: LeafRow[];
  yields: YieldRow[];
}): AnnualSummary[] {
  const years = new Map<string, AnnualSummary>();

  function bucket(year: string): AnnualSummary {
    if (!years.has(year)) {
      years.set(year, {
        year,
        yieldTotal: null,
        yieldUnit: null,
        nutrientTotals: {},
        applicationCount: 0,
        soilSampleCount: 0,
        leafSampleCount: 0,
        leafLowFlags: [],
        events: [],
      });
    }
    return years.get(year)!;
  }

  for (const a of applications) {
    const y = yearOf(a.applied_date);
    if (!y) continue;
    const b = bucket(y);
    b.applicationCount += 1;
    if (a.nutrients_kg_per_ha) {
      for (const [k, v] of Object.entries(a.nutrients_kg_per_ha)) {
        if (typeof v === "number" && !isNaN(v)) {
          b.nutrientTotals[k] = (b.nutrientTotals[k] ?? 0) + v;
        }
      }
    }
  }

  for (const e of events) {
    const y = yearOf(e.event_date);
    if (!y) continue;
    bucket(y).events.push(e);
  }

  for (const s of soil) {
    const y = yearOf(s.analysis_date) ?? yearOf(s.created_at);
    if (!y) continue;
    bucket(y).soilSampleCount += 1;
  }

  for (const l of leaf) {
    const y = yearOf(l.sample_date) ?? yearOf(l.created_at);
    if (!y) continue;
    const b = bucket(y);
    b.leafSampleCount += 1;
    if (l.classifications) {
      for (const [k, v] of Object.entries(l.classifications)) {
        if ((v === "low" || v === "deficient") && !b.leafLowFlags.includes(k)) {
          b.leafLowFlags.push(k);
        }
      }
    }
  }

  for (const yld of yields) {
    const y = pickYearFromSeason(yld.season) || yearOf(yld.harvest_date) || "";
    if (!y) continue;
    const b = bucket(y);
    // Last-write-wins if multiple yield entries share a year — the
    // last one (latest entered) typically reflects the corrected total.
    b.yieldTotal = yld.yield_actual;
    b.yieldUnit = yld.yield_unit;
  }

  return Array.from(years.values()).sort((a, b) => b.year.localeCompare(a.year));
}

/**
 * Year-over-year insight: did yield change with N applied? Returns up
 * to 2 most-recent year pairs with a delta read.
 */
export function yieldVsNitrogenInsights(summaries: AnnualSummary[]): string[] {
  const sorted = [...summaries].sort((a, b) => a.year.localeCompare(b.year));
  const out: string[] = [];
  for (let i = 1; i < sorted.length; i++) {
    const prev = sorted[i - 1];
    const cur = sorted[i];
    if (prev.yieldTotal == null || cur.yieldTotal == null) continue;
    const yieldDelta = cur.yieldTotal - prev.yieldTotal;
    const yieldPct = (yieldDelta / prev.yieldTotal) * 100;
    const nPrev = prev.nutrientTotals.N ?? 0;
    const nCur = cur.nutrientTotals.N ?? 0;
    const nDelta = nCur - nPrev;
    if (Math.abs(yieldPct) < 5 && Math.abs(nDelta) < 10) continue;
    const dir = yieldDelta >= 0 ? "↑" : "↓";
    const yLine =
      `${cur.year}: yield ${dir} ${Math.abs(yieldDelta).toFixed(1)} ${cur.yieldUnit ?? ""} ` +
      `(${yieldPct >= 0 ? "+" : ""}${yieldPct.toFixed(0)}% vs ${prev.year})`;
    const nLine = nDelta === 0
      ? "N applied unchanged"
      : `N ${nDelta >= 0 ? "+" : ""}${nDelta.toFixed(0)} kg/ha`;
    out.push(`${yLine} · ${nLine}`);
  }
  return out.slice(-2);
}
