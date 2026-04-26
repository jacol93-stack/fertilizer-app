"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ComboBox } from "@/components/client-selector";
import { toast } from "sonner";
import { Loader2, X, Save, Trash2, Copy, Layers, ChevronRight, ChevronDown } from "lucide-react";
import type { Field, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { MONTH_NAMES, IRRIGATION_TYPES, methodLabel } from "@/lib/season-constants";

interface LinkedRecord {
  id: string;
  name: string;
  type: string;
  date?: string;
  detail?: string;
}

interface ComponentSample {
  values: Record<string, number | null>;
  weight_ha?: number | null;
  location_label?: string | null;
  depth_cm?: number | null;
}

interface AnalysisComponents {
  analysis_id: string;
  composition_method: string;
  replicate_count: number;
  components: ComponentSample[];
  stats: Record<string, unknown>;
}

interface FieldDrawerProps {
  open: boolean;
  onClose: () => void;
  field: Field | null;
  farmId: string;
  crops: CropNorm[];
  analyses: SoilAnalysis[];
  onSaved: (field: Field) => void;
  onDeleted?: (fieldId: string) => void;
  onDuplicate?: (sourceField: Field) => void;
  prefill?: Partial<Field> | null;
  linkedRecords?: LinkedRecord[];
}

interface CropMethod {
  method: string;
  is_default: boolean;
  timing_notes: string | null;
}

interface FieldForm {
  name: string;
  sizeHa: string;
  gpsLat: string;
  gpsLng: string;
  soilType: string;
  crop: string;
  cultivar: string;
  cropType: string | null;
  plantingDate: string;
  treeAge: string;
  popPerHa: string;
  yieldTarget: string;
  yieldUnit: string;
  irrigationType: string;
  /** "" = unknown / not yet set, "yes" / "no" otherwise. Tri-state because
   * the demo dataset has 60-odd legacy fields where it's never been answered. */
  fertigationCapable: "" | "yes" | "no";
  acceptedMethods: string[];
  fertigationMonths: number[];
  latestAnalysisId: string;
}

function fieldToForm(f: Field): FieldForm {
  return {
    name: f.name,
    sizeHa: f.size_ha?.toString() || "",
    gpsLat: f.gps_lat?.toString() || "",
    gpsLng: f.gps_lng?.toString() || "",
    soilType: f.soil_type || "",
    crop: f.crop || "",
    cultivar: f.cultivar || "",
    cropType: f.crop_type?.toLowerCase() || null,
    plantingDate: f.planting_date || "",
    treeAge: f.tree_age?.toString() || "",
    popPerHa: f.pop_per_ha?.toString() || "",
    yieldTarget: f.yield_target?.toString() || "",
    yieldUnit: f.yield_unit || "",
    irrigationType: f.irrigation_type || "",
    fertigationCapable: f.fertigation_capable === true ? "yes" : f.fertigation_capable === false ? "no" : "",
    acceptedMethods: f.accepted_methods || [],
    fertigationMonths: f.fertigation_months || [],
    latestAnalysisId: f.latest_analysis_id || "",
  };
}

function formToPayload(f: FieldForm): Record<string, unknown> {
  return {
    name: f.name.trim(),
    size_ha: f.sizeHa ? parseFloat(f.sizeHa) : null,
    gps_lat: f.gpsLat ? parseFloat(f.gpsLat) : null,
    gps_lng: f.gpsLng ? parseFloat(f.gpsLng) : null,
    soil_type: f.soilType || null,
    crop: f.crop || null,
    cultivar: f.cultivar || null,
    crop_type: f.cropType?.toLowerCase() || null,
    planting_date: f.plantingDate || null,
    tree_age: f.treeAge ? parseInt(f.treeAge) : null,
    pop_per_ha: f.popPerHa ? parseInt(f.popPerHa) : null,
    yield_target: f.yieldTarget ? parseFloat(f.yieldTarget) : null,
    yield_unit: f.yieldUnit || null,
    irrigation_type: f.irrigationType || null,
    fertigation_capable: f.fertigationCapable === "yes" ? true : f.fertigationCapable === "no" ? false : null,
    accepted_methods: f.acceptedMethods,
    fertigation_months: f.fertigationMonths,
    latest_analysis_id: f.latestAnalysisId || null,
  };
}

export function FieldDrawer({ open, onClose, field, farmId, crops, analyses, onSaved, onDeleted, onDuplicate, prefill, linkedRecords }: FieldDrawerProps) {
  const isNew = !field;
  const [form, setForm] = useState<FieldForm>(field ? fieldToForm(field) : {
    name: "", sizeHa: "", gpsLat: "", gpsLng: "", soilType: "", crop: "", cultivar: "",
    cropType: null, plantingDate: "", treeAge: "", popPerHa: "",
    yieldTarget: "", yieldUnit: "", irrigationType: "", fertigationCapable: "",
    acceptedMethods: [], fertigationMonths: [], latestAnalysisId: "",
  });
  const [cropMethods, setCropMethods] = useState<CropMethod[]>([]);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const initialRef = useRef<string>("");
  const [components, setComponents] = useState<AnalysisComponents | null>(null);
  const [loadingComponents, setLoadingComponents] = useState(false);
  const [componentsExpanded, setComponentsExpanded] = useState(false);

  useEffect(() => {
    if (!open) return;
    const empty: FieldForm = {
      name: "", sizeHa: "", gpsLat: "", gpsLng: "", soilType: "", crop: "", cultivar: "",
      cropType: null, plantingDate: "", treeAge: "", popPerHa: "",
      yieldTarget: "", yieldUnit: "", irrigationType: "", fertigationCapable: "",
      acceptedMethods: [], fertigationMonths: [], latestAnalysisId: "",
    };
    let f: FieldForm;
    if (field) {
      f = fieldToForm(field);
    } else if (prefill) {
      // Duplicate mode: pre-fill from source field but blank the name and analysis
      const source = fieldToForm(prefill as Field);
      f = { ...source, name: "", latestAnalysisId: "" };
    } else {
      f = empty;
    }
    setForm(f);
    initialRef.current = JSON.stringify(empty); // For duplicates, form starts "dirty"
    setDirty(!field); // New/duplicate = dirty, edit = not dirty
    const cropToLoad = field?.crop || prefill?.crop;
    if (cropToLoad) loadMethods(cropToLoad);
    else setCropMethods([]);
  }, [open, field, prefill]);

  const update = (updates: Partial<FieldForm>) => {
    setForm((prev) => {
      const next = { ...prev, ...updates };
      setDirty(JSON.stringify(next) !== initialRef.current);
      return next;
    });
  };

  const loadMethods = async (cropName: string) => {
    if (!cropName) { setCropMethods([]); return; }
    try {
      const methods = await api.get<CropMethod[]>(`/api/crop-norms/${encodeURIComponent(cropName)}/methods`);
      setCropMethods(methods || []);
    } catch { setCropMethods([]); }
  };

  // Fetch the component retention panel for the currently-linked analysis.
  // Only surfaces content when the analysis is a real composite (replicate
  // count > 1); single-sample rows get the existing dropdown and nothing
  // else, matching pre-multi-sample behaviour.
  useEffect(() => {
    const id = form.latestAnalysisId;
    if (!id) {
      setComponents(null);
      setComponentsExpanded(false);
      return;
    }
    let cancelled = false;
    setLoadingComponents(true);
    api
      .get<AnalysisComponents>(`/api/soil/${id}/components`)
      .then((res) => {
        if (!cancelled) setComponents(res);
      })
      .catch(() => {
        if (!cancelled) setComponents(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingComponents(false);
      });
    return () => {
      cancelled = true;
    };
  }, [form.latestAnalysisId]);

  const handleCropSelect = async (cropName: string) => {
    const cropNorm = crops.find((c) => c.crop === cropName);
    const ct = cropNorm?.crop_type || (cropNorm as Record<string, unknown> | undefined)?.type as string | undefined || null;
    update({
      crop: cropName,
      cropType: ct?.toLowerCase() || null,
      yieldUnit: cropNorm?.yield_unit || form.yieldUnit,
    });
    await loadMethods(cropName);
  };

  const toggleMethod = (method: string) => {
    const next = form.acceptedMethods.includes(method)
      ? form.acceptedMethods.filter((m) => m !== method)
      : [...form.acceptedMethods, method];
    const fm = method === "fertigation" && form.acceptedMethods.includes(method) ? [] : form.fertigationMonths;
    update({ acceptedMethods: next, fertigationMonths: fm });
  };

  const handleSave = async () => {
    if (!form.name.trim()) { toast.error("Field name is required"); return; }
    setSaving(true);
    try {
      const data = formToPayload(form);
      let result: Field;
      if (isNew) {
        result = await api.post<Field>(`/api/clients/farms/${farmId}/fields`, data);
      } else {
        result = await api.patch<Field>(`/api/clients/fields/${field!.id}`, data);
      }
      onSaved(result);
      initialRef.current = JSON.stringify(fieldToForm(result));
      setDirty(false);
      toast.success(isNew ? "Field created" : "Field saved");
      if (isNew) onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!field) return;
    if (!confirm(`Delete field "${field.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/clients/fields/${field.id}`);
      onDeleted?.(field.id);
      onClose();
      toast.success("Field deleted");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete");
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/30" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg overflow-y-auto bg-white shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-5 py-3">
          <h2 className="text-base font-semibold text-[var(--sapling-dark)]">
            {isNew ? "Add Field" : form.name || field?.name}
          </h2>
          <div className="flex items-center gap-2">
            {!isNew && onDuplicate && field && (
              <button
                onClick={() => onDuplicate(field)}
                className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-500"
                title="Duplicate field"
              >
                <Copy className="size-4" />
              </button>
            )}
            {!isNew && (
              <button onClick={handleDelete} className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500" title="Delete field">
                <Trash2 className="size-4" />
              </button>
            )}
            <button onClick={onClose} className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100">
              <X className="size-5" />
            </button>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-5 px-5 py-4">
          {/* Basic info */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--sapling-medium-grey)]">Basic Info</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs">Field Name *</Label>
                <Input value={form.name} onChange={(e) => update({ name: e.target.value })} placeholder="e.g. Block A" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Area (ha)</Label>
                <Input type="number" step="0.1" value={form.sizeHa} onChange={(e) => update({ sizeHa: e.target.value })} />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs">GPS Latitude</Label>
                <Input type="number" step="any" value={form.gpsLat} onChange={(e) => update({ gpsLat: e.target.value })} placeholder="-25.7461" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">GPS Longitude</Label>
                <Input type="number" step="any" value={form.gpsLng} onChange={(e) => update({ gpsLng: e.target.value })} placeholder="28.1881" />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Soil Type</Label>
              <select value={form.soilType} onChange={(e) => update({ soilType: e.target.value })} className="w-full rounded-md border bg-white px-3 py-2 text-sm">
                <option value="">Select...</option>
                {["Sandy", "Sandy loam", "Loam", "Silt loam", "Clay loam", "Sandy clay loam", "Sandy clay", "Silty clay", "Clay", "Peat", "Gravel"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </section>

          {/* Crop info */}
          <section className="space-y-3 border-t pt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--sapling-medium-grey)]">Crop</h3>
            <ComboBox
              label="Crop"
              placeholder="Select crop..."
              items={crops.map((c) => ({ name: c.crop, value: c.crop }))}
              value={form.crop}
              onChange={(val) => handleCropSelect(val)}
              onSelect={(item) => handleCropSelect(item.value as string)}
            />
            {form.cropType && (
              <p className="text-xs">
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                  form.cropType === "perennial" ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"
                }`}>{form.cropType}</span>
              </p>
            )}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs">Cultivar</Label>
                <Input value={form.cultivar} onChange={(e) => update({ cultivar: e.target.value })} placeholder="Optional" />
              </div>
              {form.cropType === "perennial" ? (
                <div className="space-y-1">
                  <Label className="text-xs">Tree Age (years)</Label>
                  <Input type="number" value={form.treeAge} onChange={(e) => update({ treeAge: e.target.value })} />
                </div>
              ) : (
                <div className="space-y-1">
                  <Label className="text-xs">Planting Date</Label>
                  <Input type="date" value={form.plantingDate} onChange={(e) => update({ plantingDate: e.target.value })} />
                </div>
              )}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label className="text-xs">Pop/ha</Label>
                <Input type="number" value={form.popPerHa} onChange={(e) => update({ popPerHa: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Yield Target</Label>
                <Input type="number" value={form.yieldTarget} onChange={(e) => update({ yieldTarget: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Unit</Label>
                <Input value={form.yieldUnit} onChange={(e) => update({ yieldUnit: e.target.value })} placeholder="t/ha" />
              </div>
            </div>
          </section>

          {/* Irrigation & methods */}
          <section className="space-y-3 border-t pt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--sapling-medium-grey)]">Irrigation & Methods</h3>
            <div className="space-y-1">
              <Label className="text-xs">Irrigation Type</Label>
              <select
                value={form.irrigationType}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === "none" || !val) {
                    // Without irrigation, fertigation is impossible.
                    update({
                      irrigationType: val,
                      fertigationCapable: "no",
                      acceptedMethods: form.acceptedMethods.filter((m) => m !== "fertigation"),
                      fertigationMonths: [],
                    });
                  } else {
                    update({ irrigationType: val });
                  }
                }}
                className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              >
                <option value="">Not specified</option>
                {IRRIGATION_TYPES.map((t) => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>

            {/* Fertigation capability — separate from irrigation type
                because a drip block may or may not have an injection
                unit. Only meaningful when there's irrigation. */}
            {form.irrigationType && form.irrigationType !== "none" && (
              <div className="space-y-1">
                <Label className="text-xs">Fertigation infrastructure?</Label>
                <div className="flex gap-2">
                  {(["yes", "no"] as const).map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => {
                        const next = form.fertigationCapable === opt ? "" : opt;
                        if (next === "no") {
                          update({
                            fertigationCapable: next,
                            acceptedMethods: form.acceptedMethods.filter((m) => m !== "fertigation"),
                            fertigationMonths: [],
                          });
                        } else {
                          update({ fertigationCapable: next });
                        }
                      }}
                      className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                        form.fertigationCapable === opt
                          ? opt === "yes"
                            ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                            : "border-gray-400 bg-gray-100 text-gray-700"
                          : "border-gray-200 text-gray-600 hover:border-gray-400"
                      }`}
                    >
                      {opt === "yes" ? "Yes — injection unit fitted" : "No — irrigation only"}
                    </button>
                  ))}
                </div>
                {form.fertigationCapable === "" && (
                  <p className="text-[11px] text-amber-700">
                    Tell us once — drives whether the programme builder offers fertigation.
                  </p>
                )}
              </div>
            )}

            <div className="space-y-1">
              <Label className="text-xs">Accepted Methods</Label>
              {cropMethods.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {cropMethods.map((cm) => {
                    const checked = form.acceptedMethods.includes(cm.method);
                    const isFert = cm.method === "fertigation";
                    const noIrr = form.irrigationType === "none" || !form.irrigationType;
                    const disabled = isFert && noIrr;
                    return (
                      <button
                        key={cm.method}
                        type="button"
                        onClick={() => !disabled && toggleMethod(cm.method)}
                        disabled={disabled}
                        className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                          checked
                            ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                            : disabled
                              ? "cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300"
                              : "border-gray-200 text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {methodLabel(cm.method)}{cm.is_default ? " *" : ""}
                      </button>
                    );
                  })}
                </div>
              ) : form.crop ? (
                <p className="text-xs text-gray-400">No methods configured for this crop</p>
              ) : (
                <p className="text-xs text-gray-400">Select a crop first</p>
              )}
            </div>

            {/* Fertigation months moved to Programme Builder (Schedule
                step) — captured per-programme, not per-field. Field
                retains the accepted_methods + irrigation_type as the
                capability record only. */}
          </section>

          {/* Linked analysis */}
          {analyses.length > 0 && (
            <section className="space-y-3 border-t pt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--sapling-medium-grey)]">Linked Soil Analysis</h3>
              <select
                value={form.latestAnalysisId}
                onChange={(e) => update({ latestAnalysisId: e.target.value })}
                className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              >
                <option value="">None</option>
                {analyses.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.field || a.cultivar || a.crop || "Unknown"} — {a.crop ? `${a.crop} ` : ""}{a.analysis_date || new Date(a.created_at).toLocaleDateString()}{a.lab_name ? ` (${a.lab_name})` : ""}
                  </option>
                ))}
              </select>

              {/* Composite component panel — only when the linked analysis
                  actually came from multiple zone samples. Single-sample
                  records (legacy or deliberate) get no extra UI. */}
              {loadingComponents && (
                <div className="flex items-center gap-2 rounded-md border bg-gray-50 px-3 py-2 text-xs text-muted-foreground">
                  <Loader2 className="size-3 animate-spin" /> Loading composite…
                </div>
              )}
              {!loadingComponents && components && components.replicate_count > 1 && (
                <div className="rounded-md border border-orange-200 bg-orange-50/50">
                  <button
                    type="button"
                    onClick={() => setComponentsExpanded((v) => !v)}
                    className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium text-orange-800 hover:bg-orange-100/60"
                  >
                    {componentsExpanded ? (
                      <ChevronDown className="size-3" />
                    ) : (
                      <ChevronRight className="size-3" />
                    )}
                    <Layers className="size-3" />
                    <span>
                      {components.replicate_count} zone sample{components.replicate_count !== 1 ? "s" : ""} composited
                    </span>
                    <span className="ml-auto text-[10px] font-normal uppercase tracking-wider text-orange-700/70">
                      {components.composition_method.replace("composite_", "").replace("_", " ")}
                    </span>
                  </button>
                  {componentsExpanded && (
                    <div className="space-y-1.5 border-t border-orange-200 px-3 py-2">
                      {components.components.length === 0 && (
                        <p className="text-[11px] text-muted-foreground">
                          Component samples not retained (pre-migration record).
                        </p>
                      )}
                      {components.components.map((c, i) => {
                        const valueKeys = Object.keys(c.values || {});
                        return (
                          <div key={i} className="rounded border border-orange-100 bg-white px-2 py-1.5 text-[11px]">
                            <div className="mb-1 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
                              <span className="font-medium text-orange-800">Zone {i + 1}</span>
                              {c.location_label && <span>{c.location_label}</span>}
                              {c.weight_ha != null && <span>{c.weight_ha} ha</span>}
                              {c.depth_cm != null && <span>{c.depth_cm} cm</span>}
                            </div>
                            <div className="flex flex-wrap gap-x-3 gap-y-0.5 tabular-nums">
                              {valueKeys.map((k) => (
                                <span key={k}>
                                  <span className="text-muted-foreground">{k}:</span>{" "}
                                  {c.values[k] ?? "—"}
                                </span>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Linked records */}
          {!isNew && linkedRecords && linkedRecords.length > 0 && (
            <section className="space-y-3 border-t pt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--sapling-medium-grey)]">Records</h3>
              <div className="space-y-1.5">
                {linkedRecords.map((r) => (
                  <div key={r.id} className="flex items-center justify-between rounded-lg border bg-gray-50 px-3 py-2">
                    <div>
                      <p className="text-xs font-medium text-[var(--sapling-dark)]">{r.name}</p>
                      {r.detail && <p className="text-[10px] text-[var(--sapling-medium-grey)]">{r.detail}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        r.type === "blend" ? "bg-purple-50 text-purple-700" :
                        r.type === "programme" ? "bg-green-50 text-green-700" :
                        "bg-blue-50 text-blue-700"
                      }`}>{r.type}</span>
                      {r.date && <span className="text-[10px] text-[var(--sapling-medium-grey)]">{r.date}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 border-t bg-white px-5 py-3">
          <Button
            onClick={handleSave}
            disabled={saving || !dirty && !isNew}
            className="w-full bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
          >
            {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            {isNew ? "Create Field" : dirty ? "Save Changes" : "No Changes"}
          </Button>
        </div>
      </div>
    </>
  );
}
