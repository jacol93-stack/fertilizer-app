"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { SoilDetailView } from "@/components/soil-detail-view";
import { LeafDetailView } from "@/components/leaf-detail-view";
import type { Field } from "@/lib/season-constants";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SelectionToolbar } from "@/components/ui/selection-toolbar";
import { DocumentTray, type TrayDoc, type TrayBlock } from "@/components/client-portal/document-tray";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "sonner";
import {
  Loader2,
  ArrowLeft,
  Calendar,
  Trash2,
  FileText,
  RotateCcw,
  ExternalLink,
  X,
  LinkIcon,
  FileBarChart,
  Leaf as LeafIcon,
  Layers,
  Download,
  Lock,
} from "lucide-react";
import { listProgrammes, downloadProgrammePdf } from "@/lib/programmes-v2";
import type { ProgrammeListItem } from "@/lib/types/programme-artifact";
import { listSoilReports, downloadSoilReportPdf, type SoilReportListItem } from "@/lib/soil-reports";

// ── Types ──────────────────────────────────────────────────────────────

interface SoilAnalysis {
  id: string;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  lab_name: string | null;
  analysis_date: string | null;
  farm_id: string | null;
  field_id: string | null;
  farm: string | null;
  field: string | null;
  source_document_url: string | null;
  created_at: string;
  deleted_at?: string | null;
}

interface LeafAnalysis {
  id: string;
  crop: string | null;
  cultivar?: string | null;
  lab_name: string | null;
  sample_date: string | null;
  sample_part?: string | null;
  farm_id: string | null;
  field_id: string | null;
  source_document_url: string | null;
  values: Record<string, number | null> | null;
  classifications: Record<string, string> | null;
  foliar_recommendations?: Record<string, unknown>[] | null;
  notes?: string | null;
  created_at: string;
  deleted_at?: string | null;
}

interface Farm {
  id: string;
  name: string;
}

// ── Main Component ────────────────────────────────────────────────────

export default function DocumentsPageWrapper() {
  return (
    <Suspense>
      <DocumentsPage />
    </Suspense>
  );
}

function DocumentsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const clientId = params.id as string;
  const isAdmin = useEffectiveAdmin();
  const initialFilter = searchParams.get("filter") as "all" | "unlinked" | "deleted" | null;

  // Data
  const [clientName, setClientName] = useState("");
  const [soilAnalyses, setSoilAnalyses] = useState<SoilAnalysis[]>([]);
  const [leafAnalyses, setLeafAnalyses] = useState<LeafAnalysis[]>([]);
  const [deletedSoil, setDeletedSoil] = useState<SoilAnalysis[]>([]);
  const [deletedLeaf, setDeletedLeaf] = useState<LeafAnalysis[]>([]);
  // Sapling-generated documents (separate sub-headings from uploaded
  // lab analyses). Programmes come from programme_artifacts; soil
  // reports from soil_reports — both rendered live as PDFs on demand.
  const [programmes, setProgrammes] = useState<ProgrammeListItem[]>([]);
  const [soilReports, setSoilReports] = useState<SoilReportListItem[]>([]);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmFields, setFarmFields] = useState<Record<string, Field[]>>({});
  const [loading, setLoading] = useState(true);

  // UI state — active sub-heading. Four kinds of docs sit on this page;
  // the user toggles between them via the tab bar.
  type DocTab = "programmes" | "soil_reports" | "soil" | "leaf";
  const [activeTab, setActiveTab] = useState<DocTab>("soil");
  const [filter, setFilter] = useState<"all" | "unlinked" | "deleted">(initialFilter || "all");
  const [view, setView] = useState<"table" | "tray">(initialFilter === "unlinked" ? "tray" : "table");
  const [yearFilter, setYearFilter] = useState<string>("all");
  const [sheetRecord, setSheetRecord] = useState<{ type: "soil" | "leaf"; id: string } | null>(null);
  const [sheetData, setSheetData] = useState<Record<string, unknown> | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Bulk-select state — scoped to whichever tab + filter is active so
  // switching tabs / filters resets the selection (otherwise the user
  // would see stale ids selected across an unrelated list).
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelected = (id: string) =>
    setSelectedIds((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  // Reset selection when tab / filter changes — different rows on screen.
  useEffect(() => {
    setSelectionMode(false);
    setSelectedIds(new Set());
  }, [activeTab, filter, yearFilter]);

  // Lookup maps
  const farmMap = new Map(farms.map((f) => [f.id, f.name]));
  const fieldMap = new Map(
    Object.values(farmFields)
      .flat()
      .map((f) => [f.id, f])
  );

  const allFields = Object.entries(farmFields).flatMap(([fId, flds]) => {
    const farm = farms.find((f) => f.id === fId);
    return flds.map((f) => ({ id: f.id, name: f.name, farmName: farm?.name || "" }));
  });

  // ── Data fetching ───────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [allClients, farmsData, soilData, leafData, progData, srData] = await Promise.all([
        api.getAll<{ id: string; name: string }>("/api/clients"),
        api.get<Farm[]>(`/api/clients/${clientId}/farms`),
        api.getAll<SoilAnalysis>(`/api/soil?client_id=${clientId}`).catch(() => [] as SoilAnalysis[]),
        api.getAll<LeafAnalysis>(`/api/leaf?client_id=${clientId}`).catch(() => [] as LeafAnalysis[]),
        listProgrammes({ clientId }).catch(() => [] as ProgrammeListItem[]),
        listSoilReports({ clientId }).catch(() => [] as SoilReportListItem[]),
      ]);

      const c = allClients.find((cl) => cl.id === clientId);
      setClientName(c?.name || "Client");
      setFarms(farmsData);
      setSoilAnalyses(soilData);
      setLeafAnalyses(leafData);
      setProgrammes(progData);
      setSoilReports(srData);

      // Fetch fields per farm
      const fieldResults: Record<string, Field[]> = {};
      await Promise.all(
        farmsData.map(async (farm) => {
          try {
            fieldResults[farm.id] = await api.get<Field[]>(`/api/clients/farms/${farm.id}/fields`);
          } catch {
            fieldResults[farm.id] = [];
          }
        })
      );
      setFarmFields(fieldResults);

      // Fetch deleted records for admin
      if (isAdmin) {
        try {
          const deleted = await api.get<{ soil_analyses: SoilAnalysis[]; leaf_analyses: LeafAnalysis[] }>(
            `/api/admin/deleted?client_id=${clientId}`
          );
          setDeletedSoil(deleted.soil_analyses || []);
          setDeletedLeaf(deleted.leaf_analyses || []);
        } catch {
          // Endpoint may not support client_id filter — fall back to empty
        }
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [clientId, isAdmin]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Helpers ─────────────────────────────────────────────────────────

  function resolveFarmField(farmId: string | null, fieldId: string | null, farmText?: string | null, fieldText?: string | null) {
    const farmName = farmText || (farmId ? farmMap.get(farmId) : null) || "";
    const fieldName = fieldText || (fieldId ? fieldMap.get(fieldId)?.name : null) || "";
    if (farmName && fieldName) return `${farmName} / ${fieldName}`;
    return farmName || fieldName || "-";
  }

  // ── Actions ─────────────────────────────────────────────────────────

  async function handleDelete(type: "soil" | "leaf", id: string) {
    if (!confirm("Delete this analysis? It can be restored by an admin.")) return;
    setDeletingId(id);
    try {
      await api.post(`/api/${type}/${id}/delete`, {});
      if (type === "soil") {
        setSoilAnalyses((prev) => prev.filter((a) => a.id !== id));
      } else {
        setLeafAnalyses((prev) => prev.filter((a) => a.id !== id));
      }
      toast.success("Analysis deleted");
    } catch {
      toast.error("Failed to delete");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleBulkDelete() {
    const ids = Array.from(selectedIds);
    let ok = 0;
    let failed = 0;
    for (const id of ids) {
      try {
        await api.post(`/api/${activeTab}/${id}/delete`, {});
        ok++;
      } catch {
        failed++;
      }
    }
    if (failed === 0) {
      toast.success(`Deleted ${ok} ${activeTab} ${ok === 1 ? "analysis" : "analyses"}`);
    } else {
      toast.warning(`${ok} deleted · ${failed} failed`);
    }
    setSelectedIds(new Set());
    setSelectionMode(false);
  }

  // ── Bulk link to a chosen field ─────────────────────────────────────
  // For when the user uploaded analyses before creating blocks: select
  // the unlinked rows + pick a target block, OR ask the system to
  // match-by-name across the client's blocks.
  const [bulkLinkOpen, setBulkLinkOpen] = useState(false);
  const [bulkLinkBusy, setBulkLinkBusy] = useState(false);

  async function handleBulkLinkToField(fieldId: string) {
    setBulkLinkBusy(true);
    const ids = Array.from(selectedIds);
    let ok = 0;
    let failed = 0;
    for (const id of ids) {
      try {
        await api.post(`/api/${activeTab}/${id}/link-field`, { field_id: fieldId });
        ok++;
      } catch {
        failed++;
      }
    }
    if (failed === 0) toast.success(`Linked ${ok} ${activeTab} analyses`);
    else toast.warning(`${ok} linked · ${failed} failed`);
    setSelectedIds(new Set());
    setSelectionMode(false);
    setBulkLinkOpen(false);
    setBulkLinkBusy(false);
    fetchData();
  }

  async function handleBulkLinkByName() {
    setBulkLinkBusy(true);
    const ids = Array.from(selectedIds);
    let ok = 0;
    let unmatched = 0;
    let failed = 0;
    for (const id of ids) {
      const analysis = (activeTab === "soil" ? soilAnalyses : leafAnalyses)
        .find((a) => a.id === id);
      const labelParts: string[] = [];
      if (activeTab === "soil") {
        const s = analysis as SoilAnalysis | undefined;
        if (s?.field) labelParts.push(s.field);
      }
      const blockLabel = labelParts.find(Boolean)?.trim().toLowerCase();
      if (!blockLabel) { unmatched++; continue; }
      const match = allFields.find(
        (f) => f.name.trim().toLowerCase() === blockLabel,
      );
      if (!match) { unmatched++; continue; }
      try {
        await api.post(`/api/${activeTab}/${id}/link-field`, { field_id: match.id });
        ok++;
      } catch {
        failed++;
      }
    }
    if (unmatched === 0 && failed === 0) {
      toast.success(`Linked ${ok} analyses by block name`);
    } else {
      toast.warning(
        `${ok} linked${unmatched > 0 ? ` · ${unmatched} no-match` : ""}${failed > 0 ? ` · ${failed} failed` : ""}`,
      );
    }
    setSelectedIds(new Set());
    setSelectionMode(false);
    setBulkLinkOpen(false);
    setBulkLinkBusy(false);
    fetchData();
    await fetchData();
  }

  async function handleRestore(type: "soil" | "leaf", id: string) {
    try {
      await api.post(`/api/${type}/${id}/restore`, {});
      toast.success("Analysis restored");
      fetchData();
    } catch {
      toast.error("Failed to restore");
    }
  }

  async function handleLinkField(
    type: "soil" | "leaf",
    analysisId: string,
    fieldId: string,
  ) {
    try {
      await api.post(`/api/${type}/${analysisId}/link-field`, { field_id: fieldId });
      const fieldInfo = allFields.find((f) => f.id === fieldId);
      toast.success(`Linked to ${fieldInfo?.name || "field"}`);
      if (type === "soil") {
        const updated = await api.getAll<SoilAnalysis>(`/api/soil?client_id=${clientId}`);
        setSoilAnalyses(updated);
      } else {
        const updated = await api.getAll<LeafAnalysis>(`/api/leaf?client_id=${clientId}`);
        setLeafAnalyses(updated);
      }
    } catch {
      toast.error("Failed to link");
    }
  }

  async function handleViewDocument(type: "soil" | "leaf", id: string) {
    try {
      const res = await api.get<{ url: string }>(`/api/${type}/${id}/document`);
      if (res.url) window.open(res.url, "_blank");
    } catch {
      toast.error("No document available");
    }
  }

  async function openDetail(type: "soil" | "leaf", id: string) {
    setSheetRecord({ type, id });
    setSheetLoading(true);
    try {
      const data = await api.get<Record<string, unknown>>(`/api/${type}/${id}`);
      setSheetData(data);
    } catch {
      toast.error("Failed to load details");
    } finally {
      setSheetLoading(false);
    }
  }

  // ── Filtered lists ──────────────────────────────────────────────────

  function applyYearFilter<T extends { created_at: string }>(
    rows: T[],
    dateField: "analysis_date" | "sample_date",
  ): T[] {
    if (yearFilter === "all") return rows;
    return rows.filter((r) => {
      const d = (r as Record<string, unknown>)[dateField] as string | null | undefined;
      const fallback = d ?? r.created_at;
      if (!fallback) return false;
      return fallback.startsWith(yearFilter);
    });
  }

  const filteredSoil = applyYearFilter(
    filter === "deleted"
      ? deletedSoil
      : filter === "unlinked"
        ? soilAnalyses.filter((a) => !a.field_id)
        : soilAnalyses,
    "analysis_date",
  );

  const filteredLeaf = applyYearFilter(
    filter === "deleted"
      ? deletedLeaf
      : filter === "unlinked"
        ? leafAnalyses.filter((a) => !a.field_id)
        : leafAnalyses,
    "sample_date",
  );

  const displayList = activeTab === "soil" ? filteredSoil : filteredLeaf;

  const availableYears = (() => {
    const years = new Set<string>();
    for (const a of soilAnalyses) {
      const d = a.analysis_date ?? a.created_at;
      if (d && d.length >= 4) years.add(d.slice(0, 4));
    }
    for (const a of leafAnalyses) {
      const d = a.sample_date ?? a.created_at;
      if (d && d.length >= 4) years.add(d.slice(0, 4));
    }
    return Array.from(years).sort().reverse();
  })();

  // ── Render ──────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  return (
    <>
      <div>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
            Documents — {clientName}
          </h1>
          <p className="text-sm text-muted-foreground">
            {programmes.length} programme{programmes.length !== 1 ? "s" : ""} ·{" "}
            {soilReports.length} soil report{soilReports.length !== 1 ? "s" : ""} ·{" "}
            {soilAnalyses.length} soil · {leafAnalyses.length} leaf analyses
          </p>
        </div>

        {/* Tab bar: Programmes | Soil Reports | Soil Analyses | Leaf Analyses
            Sapling-generated documents on the left (Programmes, Soil Reports);
            uploaded lab analyses on the right (Soil, Leaf). */}
        <div className="mb-4 flex flex-wrap gap-1 rounded-lg bg-muted p-1">
          {(
            [
              { key: "programmes", label: "Programmes", icon: Layers, count: programmes.length },
              { key: "soil_reports", label: "Soil Reports", icon: FileBarChart, count: soilReports.length },
              { key: "soil", label: "Soil Analyses", icon: FileText, count: soilAnalyses.length },
              { key: "leaf", label: "Leaf Analyses", icon: LeafIcon, count: leafAnalyses.length },
            ] as const
          ).map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => { setActiveTab(tab.key); setFilter("all"); }}
                className={`flex min-w-[140px] flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                    : "text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
                }`}
              >
                <Icon className="size-3.5" />
                {tab.label}
                {tab.count > 0 && (
                  <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] tabular-nums">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Sapling-generated docs render their own tables — short-circuit
            here so we skip the analysis-specific filter chips, year picker,
            and bulk-select toolbar that don't apply. */}
        {(activeTab === "programmes" || activeTab === "soil_reports") && (
          <GeneratedDocsTable
            kind={activeTab}
            clientId={clientId}
            programmes={programmes}
            soilReports={soilReports}
          />
        )}
        {(activeTab === "programmes" || activeTab === "soil_reports") ? null : <></>}
        {(activeTab !== "programmes" && activeTab !== "soil_reports") && (
        <>
        {/* Filter chips */}
        <div className="mb-4 flex gap-2">
          {(["all", "unlinked", ...(isAdmin ? ["deleted" as const] : [])] as const).map((f) => {
            const labels = { all: "All", unlinked: "Unlinked", deleted: "Deleted" };
            const counts: Record<string, number> = {
              all: activeTab === "soil" ? soilAnalyses.length : leafAnalyses.length,
              unlinked: activeTab === "soil"
                ? soilAnalyses.filter((a) => !a.field_id).length
                : leafAnalyses.filter((a) => !a.field_id).length,
              deleted: activeTab === "soil" ? deletedSoil.length : deletedLeaf.length,
            };
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  filter === f
                    ? f === "deleted"
                      ? "border-red-300 bg-red-50 text-red-700"
                      : f === "unlinked"
                        ? "border-amber-300 bg-amber-50 text-amber-700"
                        : "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                    : "border-gray-200 text-muted-foreground hover:bg-gray-50"
                }`}
              >
                {labels[f]}
                {counts[f] > 0 && ` (${counts[f]})`}
              </button>
            );
          })}
        </div>

        {/* View toggle + year filter + bulk-select toolbar */}
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {availableYears.length > 1 ? (
              <select
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
                className="rounded-md border bg-white px-3 py-1.5 text-xs font-medium text-[var(--sapling-dark)]"
              >
                <option value="all">All years</option>
                {availableYears.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            ) : null}
            {view === "table" && filter !== "deleted" && (
              <SelectionToolbar
                selectionMode={selectionMode}
                onToggleMode={(next) => {
                  setSelectionMode(next);
                  if (!next) setSelectedIds(new Set());
                }}
                totalCount={displayList.length}
                selectedCount={selectedIds.size}
                onSelectAll={(all) => {
                  if (all) setSelectedIds(new Set(displayList.map((a) => a.id)));
                  else setSelectedIds(new Set());
                }}
                onDelete={handleBulkDelete}
                itemLabel={
                  activeTab === "soil"
                    ? { singular: "soil analysis", plural: "soil analyses" }
                    : { singular: "leaf analysis", plural: "leaf analyses" }
                }
              />
            )}
            {selectionMode && filter === "unlinked" && selectedIds.size > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setBulkLinkOpen(true)}
                className="h-8 text-xs"
              >
                <LinkIcon className="size-3.5" />
                Link {selectedIds.size}…
              </Button>
            )}
          </div>
          <div className="inline-flex gap-1 rounded-md border bg-white p-0.5">
            {(["table", "tray"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-sm px-3 py-1 text-xs font-medium transition-colors ${
                  view === v
                    ? "bg-[var(--sapling-orange)] text-white"
                    : "text-muted-foreground hover:bg-orange-50"
                }`}
              >
                {v === "table" ? "Table" : "Drag-link tray"}
              </button>
            ))}
          </div>
        </div>

        {view === "tray" ? (
          <DocumentTray
            unlinkedDocs={[
              ...soilAnalyses
                .filter((a) => !a.field_id)
                .map<TrayDoc>((a) => ({
                  id: a.id,
                  type: "soil",
                  lab_name: a.lab_name,
                  date: a.analysis_date ?? a.created_at,
                  crop: a.crop,
                  source_document_url: a.source_document_url,
                  field_id: a.field_id,
                })),
              ...leafAnalyses
                .filter((a) => !a.field_id)
                .map<TrayDoc>((a) => ({
                  id: a.id,
                  type: "leaf",
                  lab_name: a.lab_name,
                  date: a.sample_date ?? a.created_at,
                  crop: a.crop,
                  source_document_url: a.source_document_url,
                  field_id: a.field_id,
                })),
            ]}
            blocks={allFields.map<TrayBlock>((f) => {
              const fieldRow = Object.values(farmFields).flat().find((row) => row.id === f.id);
              return {
                id: f.id,
                name: f.name,
                farm_name: f.farmName,
                crop: fieldRow?.crop ?? null,
              };
            })}
            onLinked={fetchData}
          />
        ) : (
        <Card>
          <CardContent className="py-3">
            {displayList.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                {filter === "deleted"
                  ? "No deleted analyses"
                  : filter === "unlinked"
                    ? "No unlinked analyses"
                    : `No ${activeTab} analyses found`}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      {selectionMode && <th className="pb-2 pr-2 font-medium w-6"></th>}
                      <th className="pb-2 pr-4 font-medium">Crop</th>
                      <th className="pb-2 pr-4 font-medium">Cultivar</th>
                      <th className="pb-2 pr-4 font-medium">Farm / Field</th>
                      <th className="pb-2 pr-4 font-medium">Lab</th>
                      <th className="pb-2 pr-4 font-medium">Date</th>
                      <th className="pb-2 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayList.map((a) => {
                      const isSoil = activeTab === "soil";
                      const date = isSoil
                        ? (a as SoilAnalysis).analysis_date
                        : (a as LeafAnalysis).sample_date;
                      const isDeleted = filter === "deleted";
                      const isUnlinked = !a.field_id;
                      const isSelected = selectionMode && selectedIds.has(a.id);

                      return (
                        <tr
                          key={a.id}
                          onClick={() => {
                            if (selectionMode) toggleSelected(a.id);
                            else if (!isDeleted) openDetail(activeTab, a.id);
                          }}
                          className={`border-b last:border-0 ${
                            isDeleted
                              ? "opacity-60"
                              : "cursor-pointer hover:bg-gray-50"
                          } ${isUnlinked && !isDeleted ? "bg-amber-50/30" : ""} ${
                            isSelected ? "bg-orange-50/60" : ""
                          }`}
                        >
                          {selectionMode && (
                            <td className="py-2.5 pr-2">
                              <span
                                className={`flex size-3.5 items-center justify-center rounded border-2 ${
                                  isSelected
                                    ? "border-[var(--sapling-orange)] bg-[var(--sapling-orange)]"
                                    : "border-gray-300 bg-white"
                                }`}
                              >
                                {isSelected && <span className="text-[8px] leading-none text-white">✓</span>}
                              </span>
                            </td>
                          )}
                          <td className="py-2.5 pr-4 font-medium text-[var(--sapling-dark)]">
                            {a.crop || "-"}
                          </td>
                          <td className="py-2.5 pr-4">
                            {("cultivar" in a ? a.cultivar : null) || "-"}
                          </td>
                          <td className="py-2.5 pr-4 text-muted-foreground">
                            {isSoil
                              ? resolveFarmField(a.farm_id, a.field_id, (a as SoilAnalysis).farm, (a as SoilAnalysis).field)
                              : resolveFarmField(a.farm_id, a.field_id)}
                          </td>
                          <td className="py-2.5 pr-4 text-muted-foreground">
                            {a.lab_name || "-"}
                          </td>
                          <td className="py-2.5 pr-4 text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="size-3" />
                              {date
                                ? new Date(date).toLocaleDateString()
                                : new Date(a.created_at).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="py-2.5 text-right">
                            <div
                              className="flex items-center justify-end gap-1"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {/* View original document */}
                              {a.source_document_url && !isDeleted && (
                                <button
                                  onClick={() => handleViewDocument(activeTab, a.id)}
                                  className="rounded p-1 text-muted-foreground hover:bg-gray-100 hover:text-[var(--sapling-dark)]"
                                  title="View original document"
                                >
                                  <ExternalLink className="size-3.5" />
                                </button>
                              )}

                              {/* Link to field — works for soil + leaf */}
                              {isUnlinked && !isDeleted && (
                                <select
                                  defaultValue=""
                                  onChange={(e) => {
                                    if (e.target.value)
                                      handleLinkField(activeTab, a.id, e.target.value);
                                  }}
                                  className="h-7 w-32 rounded border bg-white px-1.5 text-[11px]"
                                  title="Link to field"
                                >
                                  <option value="">Link to field...</option>
                                  {allFields.map((f) => (
                                    <option key={f.id} value={f.id}>
                                      {f.farmName ? `${f.farmName} / ` : ""}{f.name}
                                    </option>
                                  ))}
                                </select>
                              )}

                              {/* Delete */}
                              {!isDeleted && (
                                <button
                                  onClick={() => handleDelete(activeTab, a.id)}
                                  disabled={deletingId === a.id}
                                  className="rounded p-1 text-muted-foreground hover:bg-red-50 hover:text-red-600"
                                  title="Delete analysis"
                                >
                                  {deletingId === a.id ? (
                                    <Loader2 className="size-3.5 animate-spin" />
                                  ) : (
                                    <Trash2 className="size-3.5" />
                                  )}
                                </button>
                              )}

                              {/* Restore (deleted only, admin) */}
                              {isDeleted && isAdmin && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRestore(activeTab, a.id)}
                                  className="h-7 text-xs"
                                >
                                  <RotateCcw className="size-3" />
                                  Restore
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
        )}
        </>
        )}
      </div>

      {/* ── Detail Sheet ───────────────────────────────────────── */}
      <Sheet
        open={!!sheetRecord}
        onOpenChange={(open) => {
          if (!open) {
            setSheetRecord(null);
            setSheetData(null);
          }
        }}
      >
        <SheetContent side="right" className="sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              {sheetRecord?.type === "soil" ? "Soil Analysis Details" : "Leaf Analysis Details"}
            </SheetTitle>
          </SheetHeader>
          <div className="px-4 pb-4">
            {sheetLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
              </div>
            ) : sheetData ? (
              sheetRecord?.type === "soil" ? (
                <SoilDetailView soil={sheetData as unknown as Parameters<typeof SoilDetailView>[0]["soil"]} />
              ) : (
                <LeafDetailView
                  leaf={{
                    ...(sheetData as unknown as Parameters<typeof LeafDetailView>[0]["leaf"]),
                    farm_name: sheetData.farm_id ? farmMap.get(String(sheetData.farm_id)) : undefined,
                    field_name: sheetData.field_id ? fieldMap.get(String(sheetData.field_id))?.name : undefined,
                  }}
                />
              )
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">Failed to load details</p>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {bulkLinkOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => !bulkLinkBusy && setBulkLinkOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="border-b px-5 py-4">
              <h3 className="text-base font-semibold text-[var(--sapling-dark)]">
                Link {selectedIds.size} {activeTab} {selectedIds.size === 1 ? "analysis" : "analyses"}
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Pick a target block, or have the system match each
                analysis to a block by the lab&apos;s block name.
              </p>
            </div>
            <div className="space-y-3 px-5 py-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                  Match by block name (lab → existing blocks)
                </label>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={bulkLinkBusy}
                  onClick={handleBulkLinkByName}
                  className="w-full justify-start text-xs"
                >
                  Match by name
                </Button>
              </div>
              <div className="border-t pt-3">
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                  Or link all to one block
                </label>
                <select
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
                  defaultValue=""
                  disabled={bulkLinkBusy}
                  onChange={(e) => {
                    if (e.target.value) handleBulkLinkToField(e.target.value);
                  }}
                >
                  <option value="">Pick a block…</option>
                  {allFields.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.farmName ? `${f.farmName} / ` : ""}{f.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 border-t px-5 py-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setBulkLinkOpen(false)}
                disabled={bulkLinkBusy}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ============================================================
// GeneratedDocsTable — sub-heading view for Sapling-generated PDFs
// ============================================================
// Renders programmes OR soil reports as a flat list with a Download
// PDF button per row. Both lists share a similar shape (id, title,
// state, generated_at, narrative_locked) so we use one component with
// a `kind` discriminator.

function GeneratedDocsTable({
  kind,
  clientId,
  programmes,
  soilReports,
}: {
  kind: "programmes" | "soil_reports";
  clientId: string;
  programmes: ProgrammeListItem[];
  soilReports: SoilReportListItem[];
}) {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  async function handleDownload(id: string) {
    setDownloadingId(id);
    try {
      if (kind === "programmes") {
        await downloadProgrammePdf(id);
      } else {
        await downloadSoilReportPdf(id);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Download failed: ${msg}`);
    } finally {
      setDownloadingId(null);
    }
  }

  if (kind === "programmes") {
    if (programmes.length === 0) {
      return (
        <Card>
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            No programmes for this client yet.{" "}
            <Link
              href={`/season-manager/new?client_id=${clientId}`}
              className="text-[var(--sapling-orange)] hover:underline"
            >
              Build a programme →
            </Link>
          </CardContent>
        </Card>
      );
    }
    return (
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/30 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Programme</th>
                <th className="px-3 py-2 font-medium">Crop</th>
                <th className="px-3 py-2 font-medium">Planting</th>
                <th className="px-3 py-2 font-medium">State</th>
                <th className="px-3 py-2 font-medium">Created</th>
                <th className="px-3 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {programmes.map((p) => (
                <tr key={p.id} className="border-b last:border-0">
                  <td className="px-3 py-2 font-medium">
                    <Link
                      href={`/season-manager/artifact/${p.id}`}
                      className="hover:text-[var(--sapling-orange)] hover:underline"
                    >
                      {p.farm_name || "—"}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{p.crop || "—"}</td>
                  <td className="px-3 py-2">{p.planting_date || "—"}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                        p.state === "draft"
                          ? "bg-slate-200 text-slate-800"
                          : p.state === "approved" || p.state === "activated"
                            ? "bg-green-100 text-green-800"
                            : "bg-stone-200 text-stone-700"
                      }`}
                    >
                      {p.state}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    {new Date(p.created_at).toLocaleDateString(undefined, {
                      year: "numeric", month: "short", day: "numeric",
                    })}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="xs"
                        onClick={() => handleDownload(p.id)}
                        disabled={downloadingId === p.id}
                      >
                        {downloadingId === p.id ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : (
                          <Download className="size-3" />
                        )}
                        PDF
                      </Button>
                      <Link
                        href={`/season-manager/artifact/${p.id}`}
                        className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs hover:bg-muted"
                      >
                        Open <ExternalLink className="size-3" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    );
  }

  // soil_reports
  if (soilReports.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-sm text-muted-foreground">
          No soil reports for this client yet.{" "}
          <Link
            href={`/clients/${clientId}/soil-reports/new`}
            className="text-[var(--sapling-orange)] hover:underline"
          >
            Generate one →
          </Link>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/30 text-left">
            <tr>
              <th className="px-3 py-2 font-medium">Title</th>
              <th className="px-3 py-2 font-medium">Scope</th>
              <th className="px-3 py-2 font-medium">Coverage</th>
              <th className="px-3 py-2 font-medium">State</th>
              <th className="px-3 py-2 font-medium">Created</th>
              <th className="px-3 py-2 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {soilReports.map((r) => (
              <tr key={r.id} className="border-b last:border-0">
                <td className="px-3 py-2 font-medium">
                  <Link
                    href={`/clients/${clientId}/soil-reports/${r.id}`}
                    className="hover:text-[var(--sapling-orange)] hover:underline"
                  >
                    {r.title || r.farm_name || "—"}
                  </Link>
                </td>
                <td className="px-3 py-2 capitalize text-xs">
                  {r.scope_kind.replace(/_/g, " ")}
                </td>
                <td className="px-3 py-2 text-xs">
                  {r.block_count} block{r.block_count !== 1 ? "s" : ""} · {r.analysis_count} analys
                  {r.analysis_count === 1 ? "is" : "es"}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      r.state === "draft"
                        ? "bg-slate-200 text-slate-800"
                        : r.state === "approved"
                          ? "bg-green-100 text-green-800"
                          : "bg-stone-200 text-stone-700"
                    }`}
                  >
                    {r.state}
                  </span>
                  {r.narrative_locked && (
                    <span className="ml-1 inline-flex items-center gap-0.5 rounded bg-slate-200 px-1.5 py-0.5 text-[9px] font-bold uppercase text-slate-700">
                      <Lock className="size-2.5" />
                      AI
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {new Date(r.created_at).toLocaleDateString(undefined, {
                    year: "numeric", month: "short", day: "numeric",
                  })}
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="xs"
                      onClick={() => handleDownload(r.id)}
                      disabled={downloadingId === r.id}
                    >
                      {downloadingId === r.id ? (
                        <Loader2 className="size-3 animate-spin" />
                      ) : (
                        <Download className="size-3" />
                      )}
                      PDF
                    </Button>
                    <Link
                      href={`/clients/${clientId}/soil-reports/${r.id}`}
                      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs hover:bg-muted"
                    >
                      Open <ExternalLink className="size-3" />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
