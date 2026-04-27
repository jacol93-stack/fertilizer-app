"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { FieldDrawer } from "@/components/farm/field-drawer";
import { BlendDetailView } from "@/components/blend-detail-view";
import { SoilDetailView } from "@/components/soil-detail-view";
import { BatchAnalysisUpload } from "@/components/batch-analysis-upload";
import type { Field, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
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
  Phone,
  Mail,
  MapPin,
  Leaf,
  FlaskConical,
  Droplets,
  Calendar,
  Plus,
  X,
  ChevronDown,
  ChevronRight,
  Pencil,
  Trash2,
  Upload,
  User,
  Layers,
  FileText,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────

interface CompanyDetails {
  company_name?: string;
  reg_number?: string;
  vat_number?: string;
  address?: string;
  phone?: string;
  email?: string;
}

interface Client {
  id: string;
  name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  company_details?: CompanyDetails | null;
}

interface Farm {
  id: string;
  name: string;
  location: string | null;
  region: string | null;
  notes: string | null;
}

interface Blend {
  id: string;
  blend_name: string | null;
  blend_type: string | null;
  cost_per_ton: number | null;
  targets: Record<string, number> | null;
  selling_price: number | null;
  farm_id: string | null;
  field_id: string | null;
  farm: string | null;
  field: string | null;
  client: string | null;
  created_at: string;
}

// v2 ProgrammeArtifact list-row shape (from /api/programmes/v2 list endpoint).
// One row per saved programme; full artifact JSON only loaded on click.
interface Programme {
  id: string;
  created_at: string;
  farm_name?: string | null;
  crop: string;
  state: string;
  blocks_count: number;
  ref_number?: string | null;
}

interface LocalSoilAnalysis {
  id: string;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  lab_name: string | null;
  analysis_date: string | null;
  total_cost_ha: number | null;
  farm_id: string | null;
  field_id: string | null;
  farm: string | null;
  field: string | null;
  created_at: string;
}

// ── Inline Dialog ──────────────────────────────────────────────────────

function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">{title}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export default function ClientHubPageWrapper() {
  return (
    <Suspense>
      <ClientHubPage />
    </Suspense>
  );
}

function ClientHubPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const clientId = params.id as string;
  const isAdmin = useEffectiveAdmin();

  // Core data
  const [client, setClient] = useState<Client | null>(null);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmFields, setFarmFields] = useState<Record<string, Field[]>>({});
  const [soilAnalyses, setSoilAnalyses] = useState<LocalSoilAnalysis[]>([]);
  const [leafAnalyses, setLeafAnalyses] = useState<Record<string, unknown>[]>([]);
  const [batchUploadOpen, setBatchUploadOpen] = useState(false);
  const [blends, setBlends] = useState<Blend[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [crops, setCrops] = useState<CropNorm[]>([]);
  const [loading, setLoading] = useState(true);

  // Farm collapse state
  const [expandedFarms, setExpandedFarms] = useState<Set<string>>(new Set());

  // Farm editing
  const [editingFarmId, setEditingFarmId] = useState<string | null>(null);
  const [editFarmName, setEditFarmName] = useState("");
  const [editFarmRegion, setEditFarmRegion] = useState("");

  // Client edit dialog
  const [editClientOpen, setEditClientOpen] = useState(false);
  const [editClient, setEditClient] = useState({ name: "", contact_person: "", email: "", phone: "" });
  const [savingClient, setSavingClient] = useState(false);

  // Add farm dialog
  const [addFarmOpen, setAddFarmOpen] = useState(false);
  const [newFarmName, setNewFarmName] = useState("");
  const [newFarmRegion, setNewFarmRegion] = useState("");
  const [savingFarm, setSavingFarm] = useState(false);

  // Field drawer
  const [fieldDrawerOpen, setFieldDrawerOpen] = useState(false);
  const [fieldDrawerField, setFieldDrawerField] = useState<Field | null>(null);
  const [fieldDrawerFarmId, setFieldDrawerFarmId] = useState("");
  const [fieldDrawerPrefill, setFieldDrawerPrefill] = useState<Partial<Field> | null>(null);

  // Detail sheet
  const [sheetRecord, setSheetRecord] = useState<{ type: "blend" | "soil"; id: string } | null>(null);
  const [sheetData, setSheetData] = useState<any>(null);
  const [sheetLoading, setSheetLoading] = useState(false);

  // ── Data fetching ───────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [allClients, farmsData, analysesData, leafData, blendsData, programmesData, cropsData] =
        await Promise.all([
          api.getAll<Client>("/api/clients"),
          api.get<Farm[]>(`/api/clients/${clientId}/farms`),
          api.getAll<LocalSoilAnalysis>(`/api/soil?client_id=${clientId}`).catch(() => [] as LocalSoilAnalysis[]),
          api.getAll<Record<string, unknown>>(`/api/leaf?client_id=${clientId}`).catch(() => [] as Record<string, unknown>[]),
          api.getAll<Blend>(`/api/blends?client_id=${clientId}`).catch(() => [] as Blend[]),
          api.get<Programme[]>(`/api/programmes/v2?client_id=${clientId}&limit=200`).catch(() => [] as Programme[]),
          api.get<CropNorm[]>("/api/crop-norms").catch(() => [] as CropNorm[]),
        ]);

      const c = allClients.find((cl) => cl.id === clientId);
      if (!c) throw new Error("Client not found");
      setClient(c);
      setFarms(farmsData);
      setSoilAnalyses(analysesData);
      setLeafAnalyses(leafData);
      setBlends(blendsData);
      setProgrammes(programmesData);
      setCrops(cropsData);

      // Expand all farms by default
      setExpandedFarms(new Set(farmsData.map((f) => f.id)));

      // Fetch fields for each farm
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
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load client");
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Sidebar quick-action triggers — sidebar / sub-page links navigate
  // here with `?action=add-farm`, `?action=upload`, or `?addFieldFarm=<id>`
  // to open the right dialog from any context. Cleared from the URL
  // once handled so refreshing doesn't re-fire.
  useEffect(() => {
    const action = searchParams.get("action");
    const addFieldFarm = searchParams.get("addFieldFarm");
    if (!action && !addFieldFarm) return;
    if (action === "add-farm") setAddFarmOpen(true);
    if (action === "upload") setBatchUploadOpen(true);
    if (addFieldFarm) {
      setFieldDrawerFarmId(addFieldFarm);
      setFieldDrawerField(null);
      setFieldDrawerPrefill(null);
      setFieldDrawerOpen(true);
    }
    router.replace(`/clients/${clientId}`, { scroll: false });
  }, [searchParams, router, clientId]);

  // ── Derived stats ───────────────────────────────────────────────────

  const totalFields = Object.values(farmFields).reduce((sum, fields) => sum + fields.length, 0);

  // ── Handlers ────────────────────────────────────────────────────────

  function toggleFarm(farmId: string) {
    setExpandedFarms((prev) => {
      const next = new Set(prev);
      if (next.has(farmId)) next.delete(farmId);
      else next.add(farmId);
      return next;
    });
  }

  function openEditClient() {
    if (!client) return;
    setEditClient({
      name: client.name,
      contact_person: client.contact_person || "",
      email: client.email || "",
      phone: client.phone || "",
    });
    setEditClientOpen(true);
  }

  async function handleSaveClient() {
    setSavingClient(true);
    try {
      await api.patch(`/api/clients/${clientId}`, {
        name: editClient.name,
        contact_person: editClient.contact_person || null,
        email: editClient.email || null,
        phone: editClient.phone || null,
      });
      setClient((prev) => prev ? { ...prev, ...editClient } : prev);
      setEditClientOpen(false);
      toast.success("Client updated");
    } catch {
      toast.error("Failed to update client");
    } finally {
      setSavingClient(false);
    }
  }

  async function handleAddFarm() {
    setSavingFarm(true);
    try {
      const farm = await api.post<Farm>(`/api/clients/${clientId}/farms`, {
        name: newFarmName,
        region: newFarmRegion || null,
      });
      setFarms((prev) => [...prev, farm]);
      setFarmFields((prev) => ({ ...prev, [farm.id]: [] }));
      setExpandedFarms((prev) => new Set([...prev, farm.id]));
      setAddFarmOpen(false);
      setNewFarmName("");
      setNewFarmRegion("");
      toast.success("Farm added");
    } catch {
      toast.error("Failed to add farm");
    } finally {
      setSavingFarm(false);
    }
  }

  async function handleSaveFarmEdit(farmId: string) {
    try {
      await api.patch(`/api/clients/farms/${farmId}`, {
        name: editFarmName,
        region: editFarmRegion || null,
      });
      setFarms((prev) => prev.map((f) => (f.id === farmId ? { ...f, name: editFarmName, region: editFarmRegion || null } : f)));
      setEditingFarmId(null);
      toast.success("Farm updated");
    } catch {
      toast.error("Failed to update farm");
    }
  }

  async function handleDeleteFarm(farmId: string, farmName: string) {
    if (!confirm(`Delete farm "${farmName}" and all its fields? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/clients/farms/${farmId}`);
      setFarms((prev) => prev.filter((f) => f.id !== farmId));
      setFarmFields((prev) => {
        const next = { ...prev };
        delete next[farmId];
        return next;
      });
      toast.success("Farm deleted");
    } catch {
      toast.error("Failed to delete farm");
    }
  }

  function openFieldDrawer(farmId: string, field: Field | null, prefill?: Partial<Field> | null) {
    setFieldDrawerFarmId(farmId);
    setFieldDrawerField(field);
    setFieldDrawerPrefill(prefill || null);
    setFieldDrawerOpen(true);
  }

  function handleDuplicate(sourceField: Field) {
    // Close current drawer, reopen in create mode with prefilled data
    setFieldDrawerOpen(false);
    setTimeout(() => {
      openFieldDrawer(sourceField.farm_id, null, sourceField);
    }, 100);
  }

  function handleFieldSaved(field: Field) {
    setFarmFields((prev) => {
      const farmId = field.farm_id;
      const existing = prev[farmId] || [];
      const idx = existing.findIndex((f) => f.id === field.id);
      if (idx >= 0) {
        const updated = [...existing];
        updated[idx] = field;
        return { ...prev, [farmId]: updated };
      }
      return { ...prev, [farmId]: [...existing, field] };
    });
    setFieldDrawerOpen(false);
  }

  function handleFieldDeleted(fieldId: string) {
    setFarmFields((prev) => {
      const next: Record<string, Field[]> = {};
      for (const [farmId, fields] of Object.entries(prev)) {
        next[farmId] = fields.filter((f) => f.id !== fieldId);
      }
      return next;
    });
    setFieldDrawerOpen(false);
  }

  async function openDetail(type: "blend" | "soil", id: string) {
    setSheetRecord({ type, id });
    setSheetData(null);
    setSheetLoading(true);
    try {
      const endpoint = type === "blend" ? `/api/blends/${id}` : `/api/soil/${id}`;
      setSheetData(await api.get(endpoint));
    } catch {
      setSheetData(null);
    } finally {
      setSheetLoading(false);
    }
  }

  // Build SoilAnalysis[] for the FieldDrawer — only those linked to the current field
  const drawerAnalyses: SoilAnalysis[] = soilAnalyses
    .filter((a) => fieldDrawerField && a.field_id === fieldDrawerField.id)
    .map((a) => ({
      id: a.id,
      crop: a.crop,
      cultivar: a.cultivar,
      field: a.field,
      field_id: a.field_id,
      lab_name: a.lab_name,
      analysis_date: a.analysis_date,
      yield_target: a.yield_target,
      yield_unit: a.yield_unit,
      created_at: a.created_at,
      nutrient_targets: null,
    }));

  // ── Loading / Error states ──────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="py-8">
        <p className="text-muted-foreground">Client not found</p>
        <Link href="/clients" className="mt-2 text-sm text-[var(--sapling-orange)] hover:underline">
          Back to clients
        </Link>
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <>
      <div>

        {/* Page header — slim. Client name + contact already in sidebar; this
         * is a contextual title for the Overview pane only. Edit lives in the
         * sidebar Settings link. */}
        <div className="mb-5 flex items-baseline justify-between">
          <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Overview</h1>
          <button
            onClick={openEditClient}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-[var(--sapling-dark)]"
          >
            <Pencil className="size-3" />
            Edit client details
          </button>
        </div>

        {/* Stats + quick actions are now in the sidebar (see ClientPortalShell).
         * The legacy in-page action bar (Add Farm, Upload Lab Results, Bulk
         * Import, Documents, New Blend, Build Programme) was removed in this
         * commit — all reachable from the sidebar without duplication. */}

        {/* ── Farms & Fields ────────────────────────────────────── */}
        <div id="farms" className="mb-8 space-y-3 scroll-mt-20">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Farms & Fields</h2>

          {farms.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">
                No farms yet. Add a farm to get started.
              </CardContent>
            </Card>
          ) : (
            farms.map((farm) => {
              const fields = farmFields[farm.id] || [];
              const isExpanded = expandedFarms.has(farm.id);
              const isEditing = editingFarmId === farm.id;

              return (
                <Card key={farm.id}>
                  <CardContent className="py-3">
                    {/* Farm header */}
                    <div className="flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => toggleFarm(farm.id)}
                        className="flex flex-1 items-center gap-2 text-left"
                      >
                        <ChevronDown
                          className={`size-4 text-muted-foreground transition-transform ${isExpanded ? "" : "-rotate-90"}`}
                        />
                        {isEditing ? (
                          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                            <Input
                              value={editFarmName}
                              onChange={(e) => setEditFarmName(e.target.value)}
                              className="h-7 w-40 text-sm"
                              placeholder="Farm name"
                            />
                            <Input
                              value={editFarmRegion}
                              onChange={(e) => setEditFarmRegion(e.target.value)}
                              className="h-7 w-32 text-sm"
                              placeholder="Region"
                            />
                            <Button
                              size="xs"
                              onClick={() => handleSaveFarmEdit(farm.id)}
                              disabled={!editFarmName.trim()}
                            >
                              Save
                            </Button>
                            <Button size="xs" variant="outline" onClick={() => setEditingFarmId(null)}>
                              Cancel
                            </Button>
                          </div>
                        ) : (
                          <>
                            <MapPin className="size-4 text-muted-foreground" />
                            <span className="font-medium text-[var(--sapling-dark)]">{farm.name}</span>
                            {farm.region && (
                              <span className="text-xs text-muted-foreground">{farm.region}</span>
                            )}
                            <span className="text-xs text-muted-foreground">
                              ({fields.length} field{fields.length !== 1 ? "s" : ""})
                            </span>
                          </>
                        )}
                      </button>

                      {!isEditing && (
                        <div className="flex items-center gap-1">
                          <Button
                            size="xs"
                            variant="ghost"
                            onClick={() => {
                              setEditingFarmId(farm.id);
                              setEditFarmName(farm.name);
                              setEditFarmRegion(farm.region || "");
                            }}
                          >
                            <Pencil className="size-3" />
                          </Button>
                          <Button
                            size="xs"
                            variant="ghost"
                            className="text-red-500 hover:text-red-600"
                            onClick={() => handleDeleteFarm(farm.id, farm.name)}
                          >
                            <Trash2 className="size-3" />
                          </Button>
                          <Button
                            size="xs"
                            variant="outline"
                            onClick={() => openFieldDrawer(farm.id, null)}
                          >
                            <Plus className="size-3" />
                            Add Field
                          </Button>
                        </div>
                      )}
                    </div>

                    {/* Fields grid */}
                    {isExpanded && fields.length > 0 && (
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        {fields.map((f) => (
                          <div
                            key={f.id}
                            role="button"
                            tabIndex={0}
                            onClick={() => router.push(`/clients/${clientId}/fields/${f.id}`)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                router.push(`/clients/${clientId}/fields/${f.id}`);
                              }
                            }}
                            className="flex cursor-pointer items-center justify-between rounded-lg border bg-white px-3 py-2.5 text-left text-sm transition-colors hover:border-[var(--sapling-orange)]/40 hover:bg-orange-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--sapling-orange)]"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-[var(--sapling-dark)]">{f.name}</span>
                                {f.crop && (
                                  <span
                                    className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                                      f.crop_type === "perennial"
                                        ? "bg-purple-50 text-purple-700"
                                        : "bg-green-50 text-green-700"
                                    }`}
                                  >
                                    {f.crop}
                                    {f.crop_type && (
                                      <span className="ml-1 opacity-70">
                                        ({f.crop_type})
                                      </span>
                                    )}
                                  </span>
                                )}
                              </div>
                              <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
                                {f.size_ha != null && <span>{f.size_ha} ha</span>}
                                {f.irrigation_type && f.irrigation_type !== "none" && (
                                  <span className="text-cyan-600">{f.irrigation_type}</span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {f.latest_analysis_composite && f.latest_analysis_composite.replicate_count > 1 && (
                                <span
                                  className="inline-flex items-center gap-0.5 rounded-full bg-orange-100 px-1.5 py-0.5 text-[10px] font-medium text-orange-700"
                                  title={`Composite of ${f.latest_analysis_composite.replicate_count} zone samples`}
                                >
                                  <Layers className="size-2.5" />
                                  {f.latest_analysis_composite.replicate_count}
                                </span>
                              )}
                              {f.latest_analysis_id ? (
                                <span className="size-2 rounded-full bg-green-500" title="Analysis linked" />
                              ) : (
                                <span className="size-2 rounded-full bg-gray-300" title="No analysis" />
                              )}
                              <button
                                type="button"
                                title="Edit field"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openFieldDrawer(farm.id, f);
                                }}
                                className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-[var(--sapling-orange)]"
                              >
                                <Pencil className="size-3.5" />
                              </button>
                              <ChevronRight className="size-3.5 text-muted-foreground" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {isExpanded && fields.length === 0 && (
                      <p className="mt-3 text-xs text-muted-foreground">
                        No fields yet.{" "}
                        <button
                          type="button"
                          onClick={() => openFieldDrawer(farm.id, null)}
                          className="text-[var(--sapling-orange)] hover:underline"
                        >
                          Add one
                        </button>
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>

        {/* ── Unlinked Lab Results Banner ──────────────────────── */}
        {(() => {
          const unlinkedCount = soilAnalyses.filter((a) => !a.field_id).length;
          if (unlinkedCount === 0) return null;
          return (
            <Link href={`/clients/${clientId}/documents?filter=unlinked`} className="mb-6 block">
              <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                <FileText className="size-4 text-amber-600" />
                <span className="text-sm font-medium text-amber-700">
                  {unlinkedCount} unlinked lab {unlinkedCount === 1 ? "result" : "results"}
                </span>
                <span className="text-xs text-amber-600">— manage in Documents</span>
              </div>
            </Link>
          );
        })()}

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
              {sheetRecord?.type === "blend" ? "Blend Details" : "Soil Analysis Details"}
            </SheetTitle>
          </SheetHeader>
          <div className="px-4 pb-4">
            {sheetLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
              </div>
            ) : sheetData ? (
              sheetRecord?.type === "blend" ? (
                <BlendDetailView blend={sheetData} isAdmin={isAdmin} />
              ) : (
                <SoilDetailView soil={sheetData} />
              )
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">Failed to load details</p>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* ── Field Drawer ───────────────────────────────────────── */}
      <FieldDrawer
        open={fieldDrawerOpen}
        onClose={() => { setFieldDrawerOpen(false); setFieldDrawerPrefill(null); }}
        field={fieldDrawerField}
        farmId={fieldDrawerFarmId}
        crops={crops}
        analyses={drawerAnalyses}
        onSaved={handleFieldSaved}
        onDeleted={handleFieldDeleted}
        onDuplicate={handleDuplicate}
        prefill={fieldDrawerPrefill}
        linkedRecords={fieldDrawerField ? [
          ...blends
            .filter((b) => b.field_id === fieldDrawerField.id)
            .map((b) => ({
              id: b.id,
              name: b.blend_name || "Unnamed blend",
              type: "blend" as const,
              date: new Date(b.created_at).toLocaleDateString(),
              detail: b.targets ? `${Math.round(b.targets.N || 0)}:${Math.round(b.targets.P || 0)}:${Math.round(b.targets.K || 0)}` : undefined,
            })),
          // Programme→field linking via the v2 artifact list isn't
          // available yet — the list endpoint omits per-block detail.
          // Could be added back by fetching each artifact's soil_snapshots,
          // but keeping the drawer fast for now.
        ] : []}
      />

      {/* ── Edit Client Dialog ─────────────────────────────────── */}
      <Dialog open={editClientOpen} onClose={() => setEditClientOpen(false)} title="Edit Client">
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="ec-name">Client Name *</Label>
            <Input
              id="ec-name"
              value={editClient.name}
              onChange={(e) => setEditClient((prev) => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ec-contact">Contact Person</Label>
            <Input
              id="ec-contact"
              value={editClient.contact_person}
              onChange={(e) => setEditClient((prev) => ({ ...prev, contact_person: e.target.value }))}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ec-email">Email</Label>
            <Input
              id="ec-email"
              type="email"
              value={editClient.email}
              onChange={(e) => setEditClient((prev) => ({ ...prev, email: e.target.value }))}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ec-phone">Phone</Label>
            <Input
              id="ec-phone"
              value={editClient.phone}
              onChange={(e) => setEditClient((prev) => ({ ...prev, phone: e.target.value }))}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setEditClientOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveClient}
              disabled={!editClient.name.trim() || savingClient}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {savingClient && <Loader2 className="size-4 animate-spin" />}
              Save Changes
            </Button>
          </div>
        </div>
      </Dialog>

      {/* ── Add Farm Dialog ────────────────────────────────────── */}
      <Dialog open={addFarmOpen} onClose={() => setAddFarmOpen(false)} title="Add Farm">
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="af-name">Farm Name *</Label>
            <Input
              id="af-name"
              value={newFarmName}
              onChange={(e) => setNewFarmName(e.target.value)}
              placeholder="Farm name"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="af-region">Region</Label>
            <Input
              id="af-region"
              value={newFarmRegion}
              onChange={(e) => setNewFarmRegion(e.target.value)}
              placeholder="e.g. Limpopo, Tzaneen"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setAddFarmOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddFarm}
              disabled={!newFarmName.trim() || savingFarm}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {savingFarm && <Loader2 className="size-4 animate-spin" />}
              Add Farm
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Batch analysis upload sheet */}
      {client && (
        <BatchAnalysisUpload
          open={batchUploadOpen}
          onClose={() => setBatchUploadOpen(false)}
          clientId={clientId}
          clientName={client.name}
          fields={
            Object.entries(farmFields).flatMap(([farmId, flds]) => {
              const farm = farms.find((f) => f.id === farmId);
              return flds.map((f) => ({
                id: f.id,
                name: f.name,
                crop: f.crop || undefined,
                cultivar: f.cultivar || undefined,
                yield_target: f.yield_target || undefined,
                yield_unit: f.yield_unit || undefined,
                farm_id: farmId,
                farm_name: farm?.name || "",
              }));
            })
          }
          onSaved={() => {
            // Refresh analyses list
            api.getAll<LocalSoilAnalysis>(`/api/soil?client_id=${clientId}`)
              .then(setSoilAnalyses)
              .catch(() => {});
            // Also refetch fields so the composite badge / analysis-linked
            // indicator reflect the new save (merges can bump replicate_count
            // on an existing row; plain saves set latest_analysis_id).
            Promise.all(
              farms.map((farm) =>
                api.get<Field[]>(`/api/clients/farms/${farm.id}/fields`)
                  .then((flds) => [farm.id, flds] as const)
                  .catch(() => [farm.id, [] as Field[]] as const),
              ),
            ).then((pairs) => setFarmFields(Object.fromEntries(pairs)));
          }}
        />
      )}
    </>
  );
}
