"use client";

/**
 * Field dashboard — per-field history view. The new home for a field's
 * agronomic story: soil + leaf trends, yield history vs benchmark, and
 * a vertical timeline of every event that touched this field (analysis
 * uploaded, programme built, application recorded, yield logged).
 *
 * Lives at /clients/[id]/fields/[fieldId] so the client page can stay
 * a slim summary + farms/fields list. Field-row clicks now navigate
 * here instead of opening a modal drawer for view-only inspection;
 * the drawer is still used for quick edit/create.
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  AlertCircle, ArrowLeft, Calendar, FlaskConical, Leaf, MapPin, Plus, TrendingUp,
} from "lucide-react";
import type { Field, SoilAnalysis } from "@/lib/season-constants";
import { Sparkline, type SparklinePoint } from "@/components/dashboard/sparkline";
import { computeFieldInsights, type Insight } from "@/lib/field-insights";

interface YieldRecord {
  id: string;
  field_id: string;
  season: string;
  yield_actual: number;
  yield_unit: string;
  harvest_date?: string | null;
  source: string;
  notes?: string | null;
  created_at: string;
}

interface YieldBenchmark {
  cultivar: string | null;
  irrigation_regime: string;
  yield_unit: string;
  low_t_per_ha: number | null;
  typical_t_per_ha: number;
  high_t_per_ha: number | null;
  source: string;
  source_tier: string;
  notes: string | null;
}

interface LeafAnalysis {
  id: string;
  field_id: string | null;
  crop: string | null;
  cultivar: string | null;
  lab_name: string | null;
  sample_date: string | null;
  values: Record<string, number> | null;
  classifications: Record<string, string> | null;
  created_at: string;
}

interface ProgrammeArtifactSummary {
  id: string;
  crop: string;
  farm_name: string | null;
  state: string;
  blocks_count: number;
  planting_date: string;
  build_date: string;
  created_at: string;
}

const SPARKLINE_NUTRIENTS = ["pH (H2O)", "Org C", "P (Bray-1)", "K", "Ca"] as const;

export default function FieldDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;
  const fieldId = params.fieldId as string;

  const [field, setField] = useState<Field | null>(null);
  const [client, setClient] = useState<{ name: string } | null>(null);
  const [farm, setFarm] = useState<{ id: string; name: string; region: string | null } | null>(null);
  const [soilAnalyses, setSoilAnalyses] = useState<SoilAnalysis[]>([]);
  const [leafAnalyses, setLeafAnalyses] = useState<LeafAnalysis[]>([]);
  const [yields, setYields] = useState<YieldRecord[]>([]);
  const [benchmarks, setBenchmarks] = useState<YieldBenchmark[]>([]);
  const [programmes, setProgrammes] = useState<ProgrammeArtifactSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const fieldData = await api.get<Field & { farms?: { id: string; name: string; region: string | null; client_id: string } }>(
          `/api/clients/fields/${fieldId}`,
        );
        setField(fieldData);
        if (fieldData.farms) {
          setFarm({ id: fieldData.farms.id, name: fieldData.farms.name, region: fieldData.farms.region });
        }
        const [allClients, soil, leaf, ys, bm, progs] = await Promise.all([
          api.getAll<{ id: string; name: string }>("/api/clients"),
          api.getAll<SoilAnalysis>(`/api/soil?field_id=${fieldId}`).catch(() => [] as SoilAnalysis[]),
          api.getAll<LeafAnalysis>(`/api/leaf?field_id=${fieldId}`).catch(() => [] as LeafAnalysis[]),
          api.get<YieldRecord[]>(`/api/clients/fields/${fieldId}/yields`).catch(() => []),
          api.get<YieldBenchmark[]>(`/api/clients/fields/${fieldId}/benchmarks`).catch(() => []),
          api.get<ProgrammeArtifactSummary[]>(`/api/programmes/v2?client_id=${clientId}&limit=200`).catch(() => []),
        ]);
        const c = allClients.find((cl) => cl.id === clientId);
        if (c) setClient({ name: c.name });
        setSoilAnalyses(soil);
        setLeafAnalyses(leaf);
        setYields(ys);
        setBenchmarks(bm);
        setProgrammes(progs);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Failed to load field");
      } finally {
        setLoading(false);
      }
    })();
  }, [clientId, fieldId]);

  // Sparkline series — sort soil analyses by date, then extract per-nutrient
  // values into one SparklinePoint[] per nutrient.
  const sparklineSeries = useMemo(() => {
    const sortedSoil = [...soilAnalyses].sort((a, b) => {
      const da = (a.analysis_date || a.created_at || "");
      const db = (b.analysis_date || b.created_at || "");
      return da.localeCompare(db);
    });
    const series: Record<string, SparklinePoint[]> = {};
    for (const nut of SPARKLINE_NUTRIENTS) {
      series[nut] = sortedSoil.map((s) => ({
        label: s.analysis_date || s.created_at?.slice(0, 10) || "",
        value: typeof s.soil_values?.[nut] === "number" ? s.soil_values[nut] : null,
      }));
    }
    return series;
  }, [soilAnalyses]);

  // Yield bar series — chronological with the cultivar-specific benchmark band
  const benchmark = benchmarks[0] ?? null;
  const sortedYields = useMemo(
    () => [...yields].sort((a, b) => (a.season || "").localeCompare(b.season || "")),
    [yields],
  );

  // Insights — sketched, computed client-side from the same data the
  // sparklines + yield bars use. Pre-canned cards: trend, persistent
  // low/high, yield vs benchmark, data gap.
  const insights = useMemo<Insight[]>(() => {
    const series = [...soilAnalyses]
      .sort((a, b) => (a.analysis_date || "").localeCompare(b.analysis_date || ""))
      .map((s) => ({
        date: s.analysis_date || s.created_at?.slice(0, 10) || "",
        values: (s.soil_values ?? {}) as Record<string, number>,
      }))
      .filter((s) => s.date);
    const ys = sortedYields.map((y) => ({ season: y.season, yield_actual: y.yield_actual }));
    const bm = benchmark
      ? { low: benchmark.low_t_per_ha, typical: benchmark.typical_t_per_ha, high: benchmark.high_t_per_ha }
      : null;
    return computeFieldInsights(series, ys, bm);
  }, [soilAnalyses, sortedYields, benchmark]);

  // Timeline — merge events from analyses, programmes, yields
  const timeline = useMemo(() => {
    type TimelineItem = {
      date: string;
      kind: "soil" | "leaf" | "yield" | "programme";
      label: string;
      detail: string;
      href?: string;
    };
    const items: TimelineItem[] = [];
    for (const s of soilAnalyses) {
      items.push({
        date: s.analysis_date || s.created_at?.slice(0, 10) || "",
        kind: "soil",
        label: "Soil analysis",
        detail: `${s.lab_name || "Lab"}${s.crop ? ` · ${s.crop}` : ""}`,
      });
    }
    for (const l of leafAnalyses) {
      items.push({
        date: l.sample_date || l.created_at?.slice(0, 10) || "",
        kind: "leaf",
        label: "Leaf analysis",
        detail: `${l.lab_name || "Lab"}${l.crop ? ` · ${l.crop}` : ""}`,
      });
    }
    for (const y of yields) {
      items.push({
        date: y.harvest_date || y.season || "",
        kind: "yield",
        label: `Yield · ${y.season}`,
        detail: `${y.yield_actual} ${y.yield_unit}${y.notes ? ` · ${y.notes}` : ""}`,
      });
    }
    for (const p of programmes) {
      items.push({
        date: p.build_date || p.created_at?.slice(0, 10) || "",
        kind: "programme",
        label: `Programme built · ${p.crop}`,
        detail: `${p.blocks_count} block${p.blocks_count !== 1 ? "s" : ""} · state: ${p.state}`,
        href: `/season-manager/artifact/${p.id}`,
      });
    }
    return items.filter((i) => i.date).sort((a, b) => b.date.localeCompare(a.date));
  }, [soilAnalyses, leafAnalyses, yields, programmes]);

  if (loading || !field) {
    return (
      <div className="text-sm text-muted-foreground">Loading field…</div>
    );
  }

  const completeness = computeCompleteness(soilAnalyses.length, leafAnalyses.length, yields.length);

  return (
    <>
      <div>

        {/* Header */}
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">{field.name}</h1>
            <div className="mt-1 flex flex-wrap gap-2 text-xs">
              {farm && (
                <span className="flex items-center gap-1 text-muted-foreground">
                  <MapPin className="size-3" /> {farm.name}
                  {farm.region && ` · ${farm.region}`}
                </span>
              )}
              {field.crop && (
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-800">
                  {field.crop}{field.cultivar && ` · ${field.cultivar}`}
                </span>
              )}
              {field.size_ha && (
                <span className="text-muted-foreground">{field.size_ha} ha</span>
              )}
              {field.tree_age != null && (
                <span className="text-muted-foreground">{field.tree_age} yr trees</span>
              )}
              {field.irrigation_type && field.irrigation_type !== "none" && (
                <span className="rounded-full bg-blue-50 px-2 py-0.5 font-medium text-blue-800">
                  {field.irrigation_type}
                  {field.fertigation_capable && " · fertigation"}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href={`/season-manager/new?client_id=${clientId}&farm_id=${farm?.id ?? ""}&farm=${encodeURIComponent(farm?.name ?? "")}&client=${encodeURIComponent(client?.name ?? "")}`}>
              <Button size="sm" className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90">
                <Calendar className="size-3.5" /> Build Programme
              </Button>
            </Link>
          </div>
        </div>

        {/* Completeness banner */}
        {completeness && (
          <Card className="mb-4 border-l-4 border-l-amber-400 bg-amber-50/40">
            <CardContent className="py-3 text-sm text-amber-900">
              {completeness}
            </CardContent>
          </Card>
        )}

        {/* Insights — sketched cards from soil + yield history */}
        {insights.length > 0 && (
          <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {insights.map((ins) => (
              <InsightCard key={ins.id} insight={ins} />
            ))}
          </div>
        )}

        {/* Sparklines row — soil trends */}
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {SPARKLINE_NUTRIENTS.map((nut) => (
            <Card key={nut} className="p-3">
              <Sparkline
                title={nut}
                points={sparklineSeries[nut]}
                width={140}
                height={40}
              />
            </Card>
          ))}
        </div>

        {/* Yields + benchmark */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-[var(--sapling-dark)]">
                  Yield history
                </h2>
                {benchmark && (
                  <p className="text-xs text-muted-foreground">
                    Benchmark for {field.crop}
                    {field.cultivar && benchmark.cultivar ? ` (${benchmark.cultivar})` : " (generic cultivar)"}
                    {" · "}{benchmark.irrigation_regime}: low {benchmark.low_t_per_ha ?? "—"} ·
                    {" "}typical <span className="font-semibold">{benchmark.typical_t_per_ha}</span> ·
                    {" "}high {benchmark.high_t_per_ha ?? "—"} {benchmark.yield_unit}
                  </p>
                )}
              </div>
            </div>

            {sortedYields.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No yield records yet — bulk-import a yield CSV from the client page or use the field drawer.
              </p>
            ) : (
              <YieldBars
                yields={sortedYields}
                benchmark={benchmark}
              />
            )}
          </CardContent>
        </Card>

        {/* Two-column: Soil analyses + Leaf analyses */}
        <div className="mb-6 grid gap-4 md:grid-cols-2">
          <HistoryList
            title={`Soil analyses (${soilAnalyses.length})`}
            empty="No soil analyses on file."
            rows={soilAnalyses.map((s) => ({
              date: s.analysis_date || s.created_at?.slice(0, 10) || "",
              primary: s.lab_name || "Lab",
              secondary: s.crop ?? "",
              href: undefined,
            }))}
            icon={<FlaskConical className="size-3.5" />}
          />
          <HistoryList
            title={`Leaf analyses (${leafAnalyses.length})`}
            empty="No leaf analyses on file."
            rows={leafAnalyses.map((l) => ({
              date: l.sample_date || l.created_at?.slice(0, 10) || "",
              primary: l.lab_name || "Lab",
              secondary: l.crop ?? "",
              href: undefined,
            }))}
            icon={<Leaf className="size-3.5" />}
          />
        </div>

        {/* Programmes touching this field */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <h2 className="mb-3 text-base font-semibold text-[var(--sapling-dark)]">
              Programmes ({programmes.length})
            </h2>
            {programmes.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No programmes built for this client yet.
              </p>
            ) : (
              <div className="space-y-1.5">
                {programmes.map((p) => (
                  <Link
                    key={p.id}
                    href={`/season-manager/artifact/${p.id}`}
                    className="flex items-center justify-between rounded-md border bg-white px-3 py-2 text-sm hover:border-[var(--sapling-orange)]/40"
                  >
                    <div>
                      <p className="font-medium text-[var(--sapling-dark)]">
                        {p.farm_name ? `${p.farm_name} — ${p.crop}` : p.crop}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {p.blocks_count} block{p.blocks_count !== 1 ? "s" : ""} · built {p.build_date}
                      </p>
                    </div>
                    <span className="rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-[var(--sapling-orange)]">
                      {p.state}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timeline — merged event feed */}
        <Card>
          <CardContent className="py-4">
            <h2 className="mb-4 text-base font-semibold text-[var(--sapling-dark)]">
              Activity timeline
            </h2>
            {timeline.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Nothing recorded yet.
              </p>
            ) : (
              <div className="relative pl-5">
                <div className="absolute bottom-0 left-1.5 top-0 w-px bg-gray-200" />
                {timeline.map((t, i) => (
                  <div key={i} className="relative mb-3 last:mb-0">
                    <div
                      className={`absolute -left-[14px] mt-1.5 size-2.5 rounded-full ${
                        t.kind === "soil"
                          ? "bg-amber-500"
                          : t.kind === "leaf"
                          ? "bg-emerald-500"
                          : t.kind === "yield"
                          ? "bg-blue-500"
                          : "bg-[var(--sapling-orange)]"
                      }`}
                    />
                    <div className="text-sm">
                      <span className="text-xs text-muted-foreground tabular-nums">{t.date}</span>
                      {" · "}
                      {t.href ? (
                        <Link href={t.href} className="font-medium text-[var(--sapling-dark)] hover:text-[var(--sapling-orange)]">
                          {t.label}
                        </Link>
                      ) : (
                        <span className="font-medium text-[var(--sapling-dark)]">{t.label}</span>
                      )}
                      <p className="text-xs text-muted-foreground">{t.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

// ─── Helpers ───────────────────────────────────────────────────────

function computeCompleteness(soil: number, leaf: number, yields: number): string | null {
  const missing: string[] = [];
  if (soil === 0) missing.push("soil analyses");
  if (leaf === 0) missing.push("leaf analyses");
  if (yields === 0) missing.push("yield records");
  if (missing.length === 0) return null;
  if (missing.length === 3) return "No history yet — upload soil/leaf analyses and yield records to see trends.";
  return `Limited data — missing ${missing.join(", ")}. Bulk-import to fill the gaps.`;
}

interface YieldBarsProps {
  yields: YieldRecord[];
  benchmark: YieldBenchmark | null;
}

function YieldBars({ yields, benchmark }: YieldBarsProps) {
  const maxValue = Math.max(
    benchmark?.high_t_per_ha ?? 0,
    benchmark?.typical_t_per_ha ?? 0,
    ...yields.map((y) => y.yield_actual),
  );
  if (!isFinite(maxValue) || maxValue <= 0) return null;
  return (
    <div className="space-y-2">
      {yields.map((y) => {
        const widthPct = Math.min(100, (y.yield_actual / maxValue) * 100);
        const lowPct = benchmark?.low_t_per_ha ? (benchmark.low_t_per_ha / maxValue) * 100 : null;
        const typPct = benchmark?.typical_t_per_ha ? (benchmark.typical_t_per_ha / maxValue) * 100 : null;
        const highPct = benchmark?.high_t_per_ha ? (benchmark.high_t_per_ha / maxValue) * 100 : null;
        const status = !benchmark
          ? null
          : benchmark.high_t_per_ha && y.yield_actual >= benchmark.high_t_per_ha
            ? "above-high"
            : benchmark.low_t_per_ha && y.yield_actual < benchmark.low_t_per_ha
              ? "below-low"
              : "in-band";
        return (
          <div key={y.id}>
            <div className="mb-0.5 flex items-baseline justify-between text-xs">
              <span className="font-medium text-[var(--sapling-dark)]">{y.season}</span>
              <span className="tabular-nums">
                {y.yield_actual} {y.yield_unit}
                {status === "above-high" && <span className="ml-1.5 rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800">above benchmark</span>}
                {status === "below-low" && <span className="ml-1.5 rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-800">below benchmark</span>}
                {status === "in-band" && <span className="ml-1.5 rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-800">in benchmark band</span>}
              </span>
            </div>
            <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-100">
              {/* Benchmark band shading */}
              {lowPct != null && highPct != null && (
                <div
                  className="absolute top-0 h-full bg-emerald-100"
                  style={{ left: `${lowPct}%`, width: `${highPct - lowPct}%` }}
                />
              )}
              {/* Typical marker */}
              {typPct != null && (
                <div
                  className="absolute top-0 h-full w-0.5 bg-emerald-700"
                  style={{ left: `${typPct}%` }}
                />
              )}
              {/* Actual yield bar */}
              <div
                className={`absolute top-0 h-full rounded-full ${
                  status === "above-high"
                    ? "bg-emerald-600"
                    : status === "below-low"
                      ? "bg-red-500"
                      : "bg-[var(--sapling-orange)]"
                }`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface HistoryListProps {
  title: string;
  empty: string;
  rows: Array<{ date: string; primary: string; secondary: string; href?: string }>;
  icon: React.ReactNode;
}

function InsightCard({ insight }: { insight: Insight }) {
  const palette = (() => {
    switch (insight.severity) {
      case "positive": return { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-900" };
      case "warn":     return { bg: "bg-amber-50",   border: "border-amber-300",   text: "text-amber-900"   };
      case "critical": return { bg: "bg-red-50",     border: "border-red-300",     text: "text-red-900"     };
      default:         return { bg: "bg-blue-50",    border: "border-blue-300",    text: "text-blue-900"    };
    }
  })();
  const Icon = (() => {
    switch (insight.kind) {
      case "trend":             return TrendingUp;
      case "persistent_low":    return AlertCircle;
      case "persistent_high":   return AlertCircle;
      case "yield_vs_benchmark":return TrendingUp;
      default:                  return AlertCircle;
    }
  })();
  return (
    <div className={`rounded-lg border ${palette.border} ${palette.bg} p-3`}>
      <div className={`flex items-start gap-2 ${palette.text}`}>
        <Icon className="mt-0.5 size-4 shrink-0" />
        <div>
          <p className="text-sm font-medium">{insight.title}</p>
          <p className="mt-0.5 text-xs opacity-80">{insight.detail}</p>
        </div>
      </div>
    </div>
  );
}

function HistoryList({ title, empty, rows, icon }: HistoryListProps) {
  return (
    <Card>
      <CardContent className="py-4">
        <h2 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">{title}</h2>
        {rows.length === 0 ? (
          <p className="py-3 text-center text-xs text-muted-foreground">{empty}</p>
        ) : (
          <ul className="space-y-1">
            {rows.map((r, i) => (
              <li key={i} className="flex items-center justify-between rounded-md border px-2.5 py-1.5 text-xs">
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  {icon}
                  <span className="tabular-nums">{r.date}</span>
                </span>
                <span className="ml-2 flex-1 truncate text-[var(--sapling-dark)]">
                  {r.primary}
                  {r.secondary && <span className="ml-1 text-muted-foreground">· {r.secondary}</span>}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
