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
} from "lucide-react";

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
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmFields, setFarmFields] = useState<Record<string, Field[]>>({});
  const [loading, setLoading] = useState(true);

  // UI state
  const [activeTab, setActiveTab] = useState<"soil" | "leaf">("soil");
  const [filter, setFilter] = useState<"all" | "unlinked" | "deleted">(initialFilter || "all");
  const [view, setView] = useState<"table" | "tray">(initialFilter === "unlinked" ? "tray" : "table");
  const [sheetRecord, setSheetRecord] = useState<{ type: "soil" | "leaf"; id: string } | null>(null);
  const [sheetData, setSheetData] = useState<Record<string, unknown> | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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
      const [allClients, farmsData, soilData, leafData] = await Promise.all([
        api.getAll<{ id: string; name: string }>("/api/clients"),
        api.get<Farm[]>(`/api/clients/${clientId}/farms`),
        api.getAll<SoilAnalysis>(`/api/soil?client_id=${clientId}`).catch(() => [] as SoilAnalysis[]),
        api.getAll<LeafAnalysis>(`/api/leaf?client_id=${clientId}`).catch(() => [] as LeafAnalysis[]),
      ]);

      const c = allClients.find((cl) => cl.id === clientId);
      setClientName(c?.name || "Client");
      setFarms(farmsData);
      setSoilAnalyses(soilData);
      setLeafAnalyses(leafData);

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

  const filteredSoil =
    filter === "deleted"
      ? deletedSoil
      : filter === "unlinked"
        ? soilAnalyses.filter((a) => !a.field_id)
        : soilAnalyses;

  const filteredLeaf =
    filter === "deleted"
      ? deletedLeaf
      : filter === "unlinked"
        ? leafAnalyses.filter((a) => !a.field_id)
        : leafAnalyses;

  const displayList = activeTab === "soil" ? filteredSoil : filteredLeaf;

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
            {soilAnalyses.length} soil · {leafAnalyses.length} leaf analyses
          </p>
        </div>

        {/* Tab bar: Soil | Leaf */}
        <div className="mb-4 flex gap-1 rounded-lg bg-muted p-1">
          {(["soil", "leaf"] as const).map((tab) => {
            const count = tab === "soil" ? soilAnalyses.length : leafAnalyses.length;
            return (
              <button
                key={tab}
                onClick={() => { setActiveTab(tab); setFilter("all"); }}
                className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                    : "text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
                }`}
              >
                {tab === "soil" ? "Soil Analyses" : "Leaf Analyses"}
                {count > 0 && (
                  <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] tabular-nums">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

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

        {/* View toggle */}
        <div className="mb-4 flex justify-end">
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

                      return (
                        <tr
                          key={a.id}
                          onClick={() => !isDeleted && openDetail(activeTab, a.id)}
                          className={`border-b last:border-0 ${
                            isDeleted
                              ? "opacity-60"
                              : "cursor-pointer hover:bg-gray-50"
                          } ${isUnlinked && !isDeleted ? "bg-amber-50/30" : ""}`}
                        >
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
    </>
  );
}
