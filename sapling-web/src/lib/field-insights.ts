/**
 * Sketched insights — pre-canned trend cards computed from a field's
 * history. No engine, no LLM, no separate artifact. Just deterministic
 * stats over the soil + leaf + yield data the field already carries.
 *
 * Conservative thresholds — minimum 3 data points before we say
 * "trending"; benchmark comparisons only when the cited band is loaded.
 * Phase 4 will replace this with the real insights_engine on v2.
 */

export type InsightSeverity = "info" | "warn" | "critical" | "positive";

export interface Insight {
  id: string;
  severity: InsightSeverity;
  kind: "trend" | "persistent_low" | "persistent_high" | "yield_vs_benchmark" | "data_gap";
  title: string;
  detail: string;
  evidence?: string;
}

interface SoilSeriesPoint {
  date: string;
  values: Record<string, number>;
}

interface YieldPoint {
  season: string;
  yield_actual: number;
}

interface BenchmarkBand {
  low?: number | null;
  typical: number;
  high?: number | null;
}

const SOIL_TREND_NUTRIENTS = ["pH (H2O)", "Org C", "P (Bray-1)", "K", "Ca", "Mg"] as const;
const PERSISTENT_LOW_BANDS: Record<string, number> = {
  // If three years all sit below this value, we flag it.
  "pH (H2O)": 5.5,
  "Org C": 1.5,
  "P (Bray-1)": 15,
  "K": 100,
  "Ca": 600,
  "Mg": 100,
  "Zn": 1.0,
  "B": 0.3,
};
const PERSISTENT_HIGH_BANDS: Record<string, number> = {
  "pH (H2O)": 7.5,
  "Na_base_sat_pct": 5,
  "Acid_sat_pct": 12,
};

/** Linear-trend slope per year. Positive = increasing. */
function slopePerYear(points: { date: string; value: number }[]): number | null {
  if (points.length < 2) return null;
  const t0 = new Date(points[0].date).getTime();
  const xs = points.map((p) => (new Date(p.date).getTime() - t0) / (1000 * 60 * 60 * 24 * 365));
  const ys = points.map((p) => p.value);
  const n = xs.length;
  const xBar = xs.reduce((s, x) => s + x, 0) / n;
  const yBar = ys.reduce((s, y) => s + y, 0) / n;
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    num += (xs[i] - xBar) * (ys[i] - yBar);
    den += (xs[i] - xBar) ** 2;
  }
  if (den === 0) return null;
  return num / den;
}

export function computeFieldInsights(
  soilSeries: SoilSeriesPoint[],
  yieldHistory: YieldPoint[],
  benchmark: BenchmarkBand | null,
): Insight[] {
  const insights: Insight[] = [];

  const sortedSoil = [...soilSeries].sort((a, b) => a.date.localeCompare(b.date));

  // ── Trends per nutrient ──
  for (const nut of SOIL_TREND_NUTRIENTS) {
    const series = sortedSoil
      .map((s) => ({ date: s.date, value: s.values[nut] }))
      .filter((p) => typeof p.value === "number") as { date: string; value: number }[];
    if (series.length < 3) continue;
    const slope = slopePerYear(series);
    if (slope == null) continue;
    const last = series[series.length - 1].value;
    const first = series[0].value;
    if (last === 0) continue;
    const pctChange = ((last - first) / Math.abs(first)) * 100;
    const yearsSpan = Math.max(
      1,
      (new Date(series[series.length - 1].date).getTime() -
        new Date(series[0].date).getTime()) /
        (1000 * 60 * 60 * 24 * 365),
    );
    if (Math.abs(pctChange) < 15) continue; // ignore noise
    const direction = pctChange > 0 ? "up" : "down";
    insights.push({
      id: `trend:${nut}`,
      severity: pctChange < -25 ? "warn" : pctChange > 25 ? "info" : "info",
      kind: "trend",
      title: `${nut} trending ${direction} ${Math.abs(pctChange).toFixed(0)}% over ${yearsSpan.toFixed(1)} years`,
      detail: `${first.toFixed(2)} → ${last.toFixed(2)} across ${series.length} samples; slope ≈ ${slope.toFixed(3)} per year.`,
    });
  }

  // ── Persistent low / high (3+ analyses all in the same band) ──
  if (sortedSoil.length >= 3) {
    for (const [nut, threshold] of Object.entries(PERSISTENT_LOW_BANDS)) {
      const recent = sortedSoil.slice(-3);
      const values = recent
        .map((s) => s.values[nut])
        .filter((v) => typeof v === "number") as number[];
      if (values.length < 3) continue;
      if (values.every((v) => v < threshold)) {
        insights.push({
          id: `low:${nut}`,
          severity: "warn",
          kind: "persistent_low",
          title: `${nut} persistently below ${threshold}`,
          detail: `${values.length} consecutive samples under threshold (${values.map((v) => v.toFixed(2)).join(", ")}). Consider corrective input.`,
        });
      }
    }
    for (const [nut, threshold] of Object.entries(PERSISTENT_HIGH_BANDS)) {
      const recent = sortedSoil.slice(-3);
      const values = recent
        .map((s) => s.values[nut])
        .filter((v) => typeof v === "number") as number[];
      if (values.length < 3) continue;
      if (values.every((v) => v > threshold)) {
        insights.push({
          id: `high:${nut}`,
          severity: "warn",
          kind: "persistent_high",
          title: `${nut} persistently above ${threshold}`,
          detail: `${values.length} consecutive samples over threshold (${values.map((v) => v.toFixed(2)).join(", ")}).`,
        });
      }
    }
  }

  // ── Yield vs benchmark ──
  if (yieldHistory.length > 0 && benchmark) {
    const recent = yieldHistory.slice(-3);
    const avg = recent.reduce((s, y) => s + y.yield_actual, 0) / recent.length;
    if (benchmark.high != null && avg >= benchmark.high) {
      insights.push({
        id: "yield:above",
        severity: "positive",
        kind: "yield_vs_benchmark",
        title: `Recent yields above benchmark`,
        detail: `Last ${recent.length} season(s) averaged ${avg.toFixed(1)} — at or above the published "high" band of ${benchmark.high}. Whatever you're doing, keep doing it.`,
      });
    } else if (benchmark.low != null && avg < benchmark.low) {
      insights.push({
        id: "yield:below",
        severity: "warn",
        kind: "yield_vs_benchmark",
        title: `Recent yields below benchmark`,
        detail: `Last ${recent.length} season(s) averaged ${avg.toFixed(1)} — under the published "low" band of ${benchmark.low}. Worth investigating: soil health, irrigation, pest pressure.`,
      });
    } else {
      insights.push({
        id: "yield:in",
        severity: "info",
        kind: "yield_vs_benchmark",
        title: `Yields tracking benchmark`,
        detail: `Last ${recent.length} season(s) averaged ${avg.toFixed(1)}, within the published band (typical ${benchmark.typical}).`,
      });
    }
  }

  // ── Data-gap warning when very sparse ──
  if (sortedSoil.length < 3 && yieldHistory.length < 3) {
    insights.push({
      id: "gap:data",
      severity: "info",
      kind: "data_gap",
      title: `Limited history`,
      detail: `Trend insights need 3+ samples or yield records. Currently ${sortedSoil.length} soil analysis${sortedSoil.length !== 1 ? "es" : ""} + ${yieldHistory.length} yield record${yieldHistory.length !== 1 ? "s" : ""}.`,
    });
  }

  return insights;
}
