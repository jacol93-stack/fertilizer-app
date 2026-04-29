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
import { SelectionToolbar } from "@/components/ui/selection-toolbar";
import {
  AlertCircle, ArrowLeft, Calendar, FlaskConical, Leaf, MapPin, Plus, Printer, Sprout, TrendingUp, Wrench,
} from "lucide-react";
import type { Field, SoilAnalysis } from "@/lib/season-constants";
import { Sparkline, type SparklinePoint } from "@/components/dashboard/sparkline";
import { computeFieldInsights, type Insight } from "@/lib/field-insights";
import { LogApplicationForm } from "@/components/field-history/log-application";
import { LogYieldForm } from "@/components/field-history/log-yield";
import { LogEventForm } from "@/components/field-history/log-event";
import { buildAnnualSummaries, yieldVsNitrogenInsights, type FieldApplicationRow, type FieldEventRow } from "@/lib/field-annual-summary";

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
  const [applications, setApplications] = useState<FieldApplicationRow[]>([]);
  const [events, setEvents] = useState<FieldEventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState<null | "application" | "yield" | "event">(null);

  // Bulk-select state — one set per data type. Only one type's
  // selection mode is active at a time so the UI stays simple.
  const [activeSelect, setActiveSelect] = useState<null | "soil" | "leaf" | "yield" | "application" | "event">(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelectId = (id: string) =>
    setSelectedIds((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  const setSelectionMode = (kind: typeof activeSelect) => {
    setActiveSelect(kind);
    setSelectedIds(new Set());
  };

  const bulkDeleteSelected = async (
    kind: NonNullable<typeof activeSelect>,
  ) => {
    const ids = Array.from(selectedIds);
    // soil + leaf use POST /{id}/delete (soft-delete RPC pattern);
    // yields/applications/events use DELETE /{path}/{id}.
    const endpoints: Record<
      NonNullable<typeof activeSelect>,
      { method: "POST" | "DELETE"; path: (id: string) => string }
    > = {
      soil:        { method: "POST",   path: (id) => `/api/soil/${id}/delete` },
      leaf:        { method: "POST",   path: (id) => `/api/leaf/${id}/delete` },
      yield:       { method: "DELETE", path: (id) => `/api/clients/yields/${id}` },
      application: { method: "DELETE", path: (id) => `/api/clients/applications/${id}` },
      event:       { method: "DELETE", path: (id) => `/api/clients/events/${id}` },
    };
    let ok = 0;
    let failed = 0;
    const cfg = endpoints[kind];
    for (const id of ids) {
      try {
        if (cfg.method === "POST") await api.post(cfg.path(id), {});
        else await api.delete(cfg.path(id));
        ok++;
      } catch {
        failed++;
      }
    }
    if (failed === 0) {
      toast.success(`Deleted ${ok} ${kind}${ok === 1 ? "" : "s"}`);
    } else {
      toast.warning(`${ok} deleted · ${failed} failed`);
    }
    setSelectedIds(new Set());
    setActiveSelect(null);
    await reload();
  };

  const reload = async () => {
    const [soil, leaf, ys, apps, evts] = await Promise.all([
      api.getAll<SoilAnalysis>(`/api/soil?field_id=${fieldId}`).catch(() => [] as SoilAnalysis[]),
      api.getAll<LeafAnalysis>(`/api/leaf?field_id=${fieldId}`).catch(() => [] as LeafAnalysis[]),
      api.get<YieldRecord[]>(`/api/clients/fields/${fieldId}/yields`).catch(() => []),
      api.get<FieldApplicationRow[]>(`/api/clients/fields/${fieldId}/applications`).catch(() => []),
      api.get<FieldEventRow[]>(`/api/clients/fields/${fieldId}/events`).catch(() => []),
    ]);
    setSoilAnalyses(soil);
    setLeafAnalyses(leaf);
    setYields(ys);
    setApplications(apps);
    setEvents(evts);
  };

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
        const [allClients, soil, leaf, ys, bm, progs, apps, evts] = await Promise.all([
          api.getAll<{ id: string; name: string }>("/api/clients"),
          api.getAll<SoilAnalysis>(`/api/soil?field_id=${fieldId}`).catch(() => [] as SoilAnalysis[]),
          api.getAll<LeafAnalysis>(`/api/leaf?field_id=${fieldId}`).catch(() => [] as LeafAnalysis[]),
          api.get<YieldRecord[]>(`/api/clients/fields/${fieldId}/yields`).catch(() => []),
          api.get<YieldBenchmark[]>(`/api/clients/fields/${fieldId}/benchmarks`).catch(() => []),
          api.get<ProgrammeArtifactSummary[]>(`/api/programmes/v2?client_id=${clientId}&limit=200`).catch(() => []),
          api.get<FieldApplicationRow[]>(`/api/clients/fields/${fieldId}/applications`).catch(() => []),
          api.get<FieldEventRow[]>(`/api/clients/fields/${fieldId}/events`).catch(() => []),
        ]);
        const c = allClients.find((cl) => cl.id === clientId);
        if (c) setClient({ name: c.name });
        setSoilAnalyses(soil);
        setLeafAnalyses(leaf);
        setYields(ys);
        setBenchmarks(bm);
        setProgrammes(progs);
        setApplications(apps);
        setEvents(evts);
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

  // Timeline — merge every event type onto one chronological feed
  const timeline = useMemo(() => {
    type TimelineItem = {
      date: string;
      kind: "soil" | "leaf" | "yield" | "programme" | "application" | "event";
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
    for (const a of applications) {
      const nuts = a.nutrients_kg_per_ha
        ? Object.entries(a.nutrients_kg_per_ha)
            .filter(([, v]) => typeof v === "number" && v > 0)
            .map(([k, v]) => `${k} ${v}`)
            .join(" · ")
        : "";
      items.push({
        date: a.applied_date,
        kind: "application",
        label: a.product_label || "Application",
        detail: [
          a.method,
          a.rate_kg_ha ? `${a.rate_kg_ha} kg/ha` : null,
          a.rate_l_ha ? `${a.rate_l_ha} L/ha` : null,
          nuts || null,
        ].filter(Boolean).join(" · "),
      });
    }
    for (const e of events) {
      items.push({
        date: e.event_date,
        kind: "event",
        label: e.title,
        detail: `${e.event_type.replace("_", " ")}${e.description ? ` — ${e.description}` : ""}`,
      });
    }
    return items.filter((i) => i.date).sort((a, b) => b.date.localeCompare(a.date));
  }, [soilAnalyses, leafAnalyses, yields, programmes, applications, events]);

  // Annual summary roll-ups
  const annualSummaries = useMemo(
    () => buildAnnualSummaries({ applications, events, soil: soilAnalyses, leaf: leafAnalyses, yields }),
    [applications, events, soilAnalyses, leafAnalyses, yields],
  );
  const yoyInsights = useMemo(
    () => yieldVsNitrogenInsights(annualSummaries),
    [annualSummaries],
  );

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

        {/* Data inventory band — at-a-glance "what we know about this
            block, and from when". Drives the agronomist to upload
            the missing pieces before building a programme. */}
        <DataInventoryBand
          field={field}
          soilAnalyses={soilAnalyses}
          leafAnalyses={leafAnalyses}
          yields={yields}
          applications={applications}
          events={events}
        />

        {/* Quick log toolbar — feeds the historical-analysis pipeline */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-white px-3 py-2">
          <div className="text-xs text-muted-foreground">
            Quick log:
          </div>
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setOpenForm(openForm === "application" ? null : "application")}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
                openForm === "application"
                  ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                  : "bg-white hover:bg-orange-50"
              }`}
            >
              <Sprout className="size-3" /> Application
            </button>
            <button
              onClick={() => setOpenForm(openForm === "yield" ? null : "yield")}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
                openForm === "yield"
                  ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                  : "bg-white hover:bg-orange-50"
              }`}
            >
              <TrendingUp className="size-3" /> Yield
            </button>
            <button
              onClick={() => setOpenForm(openForm === "event" ? null : "event")}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
                openForm === "event"
                  ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                  : "bg-white hover:bg-orange-50"
              }`}
            >
              <Wrench className="size-3" /> Event
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1 rounded-md border bg-white px-2 py-1 text-xs hover:bg-gray-50"
              title="Print field report"
            >
              <Printer className="size-3" /> Print report
            </button>
          </div>
        </div>

        {openForm === "application" && (
          <div className="mb-4">
            <LogApplicationForm
              fieldId={fieldId}
              onSaved={async () => {
                await reload();
                setOpenForm(null);
              }}
              onCancel={() => setOpenForm(null)}
            />
          </div>
        )}
        {openForm === "yield" && (
          <div className="mb-4">
            <LogYieldForm
              fieldId={fieldId}
              defaultUnit={field.yield_unit ?? "t/ha"}
              onSaved={async () => {
                await reload();
                setOpenForm(null);
              }}
              onCancel={() => setOpenForm(null)}
            />
          </div>
        )}
        {openForm === "event" && (
          <div className="mb-4">
            <LogEventForm
              fieldId={fieldId}
              onSaved={async () => {
                await reload();
                setOpenForm(null);
              }}
              onCancel={() => setOpenForm(null)}
            />
          </div>
        )}

        {/* Annual summary — one card per year */}
        {annualSummaries.length > 0 && (
          <Card className="mb-4">
            <CardContent className="py-4">
              <div className="mb-3 flex items-baseline justify-between">
                <h2 className="text-base font-semibold text-[var(--sapling-dark)]">
                  Annual summary
                </h2>
                {yoyInsights.length > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {yoyInsights.join(" · ")}
                  </span>
                )}
              </div>
              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                {annualSummaries.map((s) => (
                  <div key={s.year} className="rounded-lg border bg-white p-3">
                    <div className="flex items-baseline justify-between">
                      <span className="text-base font-semibold text-[var(--sapling-dark)]">{s.year}</span>
                      {s.yieldTotal != null && (
                        <span className="text-sm font-semibold text-[var(--sapling-dark)] tabular-nums">
                          {s.yieldTotal} <span className="text-[10px] font-normal text-muted-foreground">{s.yieldUnit}</span>
                        </span>
                      )}
                    </div>
                    <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
                      {Object.entries(s.nutrientTotals).map(([n, v]) => (
                        <span key={n}>
                          <span className="font-semibold text-[var(--sapling-dark)] tabular-nums">{v.toFixed(0)}</span>{" "}
                          {n}
                        </span>
                      ))}
                      {Object.keys(s.nutrientTotals).length === 0 && (
                        <span className="italic">no applications logged</span>
                      )}
                    </div>
                    <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-muted-foreground">
                      {s.soilSampleCount > 0 && <span>{s.soilSampleCount} soil</span>}
                      {s.leafSampleCount > 0 && <span>{s.leafSampleCount} leaf</span>}
                      {s.applicationCount > 0 && <span>{s.applicationCount} apps</span>}
                      {s.events.length > 0 && <span>{s.events.length} events</span>}
                    </div>
                    {s.leafLowFlags.length > 0 && (
                      <div className="mt-1.5 text-[11px] text-amber-700">
                        Low: {s.leafLowFlags.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

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
              id: s.id,
              date: s.analysis_date || s.created_at?.slice(0, 10) || "",
              primary: s.lab_name || "Lab",
              secondary: s.crop ?? "",
              href: undefined,
            }))}
            icon={<FlaskConical className="size-3.5" />}
            selectionMode={activeSelect === "soil"}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelectId}
            toolbar={
              <SelectionToolbar
                selectionMode={activeSelect === "soil"}
                onToggleMode={(next) => setSelectionMode(next ? "soil" : null)}
                totalCount={soilAnalyses.length}
                selectedCount={activeSelect === "soil" ? selectedIds.size : 0}
                onSelectAll={(all) => {
                  if (all) setSelectedIds(new Set(soilAnalyses.map((s) => s.id)));
                  else setSelectedIds(new Set());
                }}
                onDelete={() => bulkDeleteSelected("soil")}
                itemLabel={{ singular: "soil analysis", plural: "soil analyses" }}
              />
            }
          />
          <HistoryList
            title={`Leaf analyses (${leafAnalyses.length})`}
            empty="No leaf analyses on file."
            rows={leafAnalyses.map((l) => ({
              id: l.id,
              date: l.sample_date || l.created_at?.slice(0, 10) || "",
              primary: l.lab_name || "Lab",
              secondary: l.crop ?? "",
              href: undefined,
            }))}
            icon={<Leaf className="size-3.5" />}
            selectionMode={activeSelect === "leaf"}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelectId}
            toolbar={
              <SelectionToolbar
                selectionMode={activeSelect === "leaf"}
                onToggleMode={(next) => setSelectionMode(next ? "leaf" : null)}
                totalCount={leafAnalyses.length}
                selectedCount={activeSelect === "leaf" ? selectedIds.size : 0}
                onSelectAll={(all) => {
                  if (all) setSelectedIds(new Set(leafAnalyses.map((l) => l.id)));
                  else setSelectedIds(new Set());
                }}
                onDelete={() => bulkDeleteSelected("leaf")}
                itemLabel={{ singular: "leaf analysis", plural: "leaf analyses" }}
              />
            }
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
                          : t.kind === "application"
                          ? "bg-violet-500"
                          : t.kind === "event"
                          ? "bg-pink-500"
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

interface HistoryListRow {
  /** Stable identifier for selection / delete dispatch. */
  id: string;
  date: string;
  primary: string;
  secondary: string;
  href?: string;
}


// ── Data inventory band ────────────────────────────────────────────
//
// Compact "what we know about this block + when" strip. Six tiles —
// data completeness, soil, leaf, yield, applications, events — each
// showing count + most-recent date. Tiles missing data render in a
// muted / amber style so the agronomist sees the gap immediately.

function DataInventoryBand({
  field,
  soilAnalyses,
  leafAnalyses,
  yields,
  applications,
  events,
}: {
  field: Field;
  soilAnalyses: SoilAnalysis[];
  leafAnalyses: LeafAnalysis[];
  yields: YieldRecord[];
  applications: FieldApplicationRow[];
  events: FieldEventRow[];
}) {
  const latestSoil = soilAnalyses
    .map((s) => s.analysis_date || s.created_at?.slice(0, 10))
    .filter(Boolean)
    .sort()
    .at(-1);
  const latestLeaf = leafAnalyses
    .map((l) => l.sample_date || l.created_at?.slice(0, 10))
    .filter(Boolean)
    .sort()
    .at(-1);
  const latestYield = yields
    .map((y) => y.season)
    .filter(Boolean)
    .sort()
    .at(-1);
  const latestApp = applications
    .map((a) => (a as { applied_at?: string; created_at?: string }).applied_at || (a as { created_at?: string }).created_at?.slice(0, 10))
    .filter(Boolean)
    .sort()
    .at(-1);
  const latestEvt = events
    .map((e) => (e as { event_date?: string; created_at?: string }).event_date || (e as { created_at?: string }).created_at?.slice(0, 10))
    .filter(Boolean)
    .sort()
    .at(-1);

  const completenessLabel = (() => {
    if (!field.health) return { label: "Unknown", tone: "muted" } as const;
    if (field.health.level === "critical") return { label: `Missing: ${field.health.critical.length}`, tone: "danger" } as const;
    if (field.health.level === "warn") return { label: `Assumes: ${field.health.warnings.length}`, tone: "warn" } as const;
    return { label: "Ready", tone: "ok" } as const;
  })();

  return (
    <div className="mb-4 grid grid-cols-2 gap-2 rounded-lg border bg-white p-3 sm:grid-cols-3 lg:grid-cols-6">
      <InventoryTile
        label="Completeness"
        value={completenessLabel.label}
        sub={field.health
          ? (field.health.level === "ok"
            ? "All inputs present"
            : (field.health.level === "critical"
              ? field.health.critical.slice(0, 3).join(", ")
              : field.health.warnings.slice(0, 2).join(", ")))
          : "—"}
        tone={completenessLabel.tone}
      />
      <InventoryTile
        label="Soil"
        value={soilAnalyses.length === 0 ? "None" : `${soilAnalyses.length} on file`}
        sub={latestSoil ? `Latest ${latestSoil}` : "Upload one to plan"}
        tone={soilAnalyses.length === 0 ? "danger" : "ok"}
      />
      <InventoryTile
        label="Leaf"
        value={leafAnalyses.length === 0 ? "None" : `${leafAnalyses.length} on file`}
        sub={latestLeaf ? `Latest ${latestLeaf}` : "Optional"}
        tone={leafAnalyses.length === 0 ? "muted" : "ok"}
      />
      <InventoryTile
        label="Yield"
        value={yields.length === 0 ? "None" : `${yields.length} season${yields.length === 1 ? "" : "s"}`}
        sub={latestYield ? `Latest ${latestYield}` : "Optional"}
        tone={yields.length === 0 ? "muted" : "ok"}
      />
      <InventoryTile
        label="Applications"
        value={applications.length === 0 ? "None" : `${applications.length} logged`}
        sub={latestApp ? `Latest ${latestApp}` : "Log as you apply"}
        tone={applications.length === 0 ? "muted" : "ok"}
      />
      <InventoryTile
        label="Events"
        value={events.length === 0 ? "None" : `${events.length} logged`}
        sub={latestEvt ? `Latest ${latestEvt}` : "Optional"}
        tone={events.length === 0 ? "muted" : "ok"}
      />
    </div>
  );
}

function InventoryTile({
  label, value, sub, tone,
}: {
  label: string;
  value: string;
  sub: string;
  tone: "ok" | "warn" | "danger" | "muted";
}) {
  const palette = {
    ok:     { bg: "bg-emerald-50/50", border: "border-emerald-200", value: "text-emerald-900", sub: "text-emerald-700/80" },
    warn:   { bg: "bg-amber-50/60",   border: "border-amber-200",   value: "text-amber-900",   sub: "text-amber-700/80"  },
    danger: { bg: "bg-red-50/60",     border: "border-red-200",     value: "text-red-900",     sub: "text-red-700/80"    },
    muted:  { bg: "bg-gray-50",       border: "border-gray-200",    value: "text-gray-700",    sub: "text-gray-500"      },
  }[tone];
  return (
    <div className={`rounded-md border ${palette.border} ${palette.bg} px-2.5 py-2`}>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className={`mt-0.5 text-sm font-semibold ${palette.value}`}>{value}</p>
      <p className={`text-[10px] ${palette.sub}`}>{sub}</p>
    </div>
  );
}

interface HistoryListProps {
  title: string;
  empty: string;
  rows: HistoryListRow[];
  icon: React.ReactNode;
  /** Bulk-select state. When `selectionMode` is true the row click
   * toggles `selectedIds` instead of navigating. The toolbar is
   * rendered alongside the title. */
  selectionMode?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
  toolbar?: React.ReactNode;
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

function HistoryList({
  title, empty, rows, icon, selectionMode, selectedIds, onToggleSelect, toolbar,
}: HistoryListProps) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--sapling-dark)]">{title}</h2>
          {toolbar}
        </div>
        {rows.length === 0 ? (
          <p className="py-3 text-center text-xs text-muted-foreground">{empty}</p>
        ) : (
          <ul className="space-y-1">
            {rows.map((r) => {
              const isSelected = selectionMode && selectedIds?.has(r.id);
              const baseClass = `flex items-center justify-between rounded-md border px-2.5 py-1.5 text-xs ${
                isSelected ? "border-[var(--sapling-orange)] bg-orange-50/40" : ""
              }`;
              return (
                <li
                  key={r.id}
                  onClick={selectionMode && onToggleSelect ? () => onToggleSelect(r.id) : undefined}
                  className={`${baseClass} ${selectionMode ? "cursor-pointer" : ""}`}
                >
                  {selectionMode && (
                    <span
                      className={`mr-2 flex size-3.5 items-center justify-center rounded border-2 ${
                        isSelected
                          ? "border-[var(--sapling-orange)] bg-[var(--sapling-orange)]"
                          : "border-gray-300 bg-white"
                      }`}
                    >
                      {isSelected && <span className="text-[8px] leading-none text-white">✓</span>}
                    </span>
                  )}
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    {icon}
                    <span className="tabular-nums">{r.date}</span>
                  </span>
                  <span className="ml-2 flex-1 truncate text-[var(--sapling-dark)]">
                    {r.primary}
                    {r.secondary && <span className="ml-1 text-muted-foreground">· {r.secondary}</span>}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
