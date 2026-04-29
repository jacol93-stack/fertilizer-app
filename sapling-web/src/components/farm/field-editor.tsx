"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ComboBox } from "@/components/client-selector";
import { toast } from "sonner";
import { Loader2, Plus, Copy, X, Save } from "lucide-react";
import type { Field, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { IRRIGATION_TYPES, methodLabel } from "@/lib/season-constants";

interface FieldEditorProps {
  open: boolean;
  onClose: () => void;
  field: Field | null; // null = creating new
  farmId: string;
  crops: CropNorm[];
  analyses: SoilAnalysis[];
  existingFieldNames: string[];
  onSaved: (field: Field) => void;
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
  fertigationCapable: "" | "yes" | "no";
  acceptedMethods: string[];
  latestAnalysisId: string;
  cropMethods: CropMethod[];
}

const EMPTY_FORM: FieldForm = {
  name: "", sizeHa: "", gpsLat: "", gpsLng: "", soilType: "", crop: "", cultivar: "",
  cropType: null, plantingDate: "", treeAge: "", popPerHa: "",
  yieldTarget: "", yieldUnit: "", irrigationType: "", fertigationCapable: "",
  acceptedMethods: [], latestAnalysisId: "",
  cropMethods: [],
};

function formFromField(f: Field): FieldForm {
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
    latestAnalysisId: f.latest_analysis_id || "",
    cropMethods: [],
  };
}

export function FieldEditor({ open, onClose, field, farmId, crops, analyses, existingFieldNames, onSaved }: FieldEditorProps) {
  const isEdit = !!field;

  // Multi-field: array of forms for new fields, single form for editing
  const [forms, setForms] = useState<FieldForm[]>([{ ...EMPTY_FORM }]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [saving, setSaving] = useState(false);

  // Reset forms when editor opens
  useEffect(() => {
    if (!open) return;
    if (field) {
      const f = formFromField(field);
      setForms([f]);
      setActiveIdx(0);
      if (field.crop) loadMethodsForForm(0, field.crop, [f]);
    } else {
      setForms([{ ...EMPTY_FORM }]);
      setActiveIdx(0);
    }
  }, [open, field]);

  const loadMethodsForForm = async (idx: number, cropName: string, currentForms?: FieldForm[]) => {
    if (!cropName) return;
    try {
      const methods = await api.get<CropMethod[]>(`/api/crop-norms/${encodeURIComponent(cropName)}/methods`);
      setForms((prev) => {
        const base = currentForms || prev;
        const updated = [...base];
        if (updated[idx]) {
          updated[idx] = { ...updated[idx], cropMethods: methods || [] };
          const validNames = (methods || []).map((m) => m.method);
          updated[idx].acceptedMethods = updated[idx].acceptedMethods.filter((m) => validNames.includes(m));
        }
        return updated;
      });
    } catch {}
  };

  const updateForm = (idx: number, updates: Partial<FieldForm>) => {
    setForms((prev) => prev.map((f, i) => i === idx ? { ...f, ...updates } : f));
  };

  const handleCropSelect = async (idx: number, cropName: string) => {
    const cropNorm = crops.find((c) => c.crop === cropName);
    const ct = cropNorm?.crop_type || (cropNorm as Record<string, unknown> | undefined)?.type as string | undefined || null;
    updateForm(idx, {
      crop: cropName,
      cropType: ct?.toLowerCase() || null,
      yieldUnit: cropNorm?.yield_unit || "",
    });
    await loadMethodsForForm(idx, cropName);
  };

  const toggleMethod = (idx: number, method: string) => {
    setForms((prev) => {
      const updated = [...prev];
      const f = { ...updated[idx] };
      if (f.acceptedMethods.includes(method)) {
        f.acceptedMethods = f.acceptedMethods.filter((m) => m !== method);
      } else {
        f.acceptedMethods = [...f.acceptedMethods, method];
      }
      updated[idx] = f;
      return updated;
    });
  };

  const addField = () => {
    setForms((prev) => [...prev, { ...EMPTY_FORM }]);
    setActiveIdx(forms.length);
  };

  const duplicateField = (idx: number) => {
    const source = forms[idx];
    const dup = { ...source, name: "" }; // Copy everything, blank the name
    setForms((prev) => [...prev, dup]);
    setActiveIdx(forms.length);
    // Load methods for the duplicate
    if (dup.crop) loadMethodsForForm(forms.length, dup.crop, [...forms, dup]);
    toast.success("Field duplicated — enter a new name");
  };

  const removeField = (idx: number) => {
    if (forms.length <= 1) return;
    setForms((prev) => prev.filter((_, i) => i !== idx));
    setActiveIdx((prev) => Math.min(prev, forms.length - 2));
  };

  const handleSave = async () => {
    // Validate all forms
    const newNames: string[] = [];
    for (let i = 0; i < forms.length; i++) {
      const f = forms[i];
      if (!f.name.trim()) {
        setActiveIdx(i);
        toast.error(`Field ${i + 1}: name is required`);
        return;
      }
      const lower = f.name.trim().toLowerCase();
      // Check against existing fields on the farm (skip if editing that same field)
      if (!isEdit && existingFieldNames.includes(lower)) {
        setActiveIdx(i);
        toast.error(`"${f.name.trim()}" already exists on this farm`);
        return;
      }
      // Check against other new fields in this batch
      if (newNames.includes(lower)) {
        setActiveIdx(i);
        toast.error(`"${f.name.trim()}" is duplicated in this batch`);
        return;
      }
      newNames.push(lower);
    }

    setSaving(true);
    try {
      for (const f of forms) {
        const data: Record<string, unknown> = {
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
          latest_analysis_id: f.latestAnalysisId || null,
        };

        let result: Field;
        if (isEdit) {
          result = await api.patch<Field>(`/api/clients/fields/${field!.id}`, data);
        } else {
          result = await api.post<Field>(`/api/clients/farms/${farmId}/fields`, data);
        }
        onSaved(result);
      }
      toast.success(isEdit ? "Field updated" : `${forms.length} field${forms.length > 1 ? "s" : ""} created`);
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  const form = forms[activeIdx] || forms[0];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-4 pt-[3vh]">
      <div className="w-full max-w-4xl rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
            {isEdit ? `Edit: ${field?.name}` : "Add Fields"}
          </h2>
          <button onClick={onClose} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="size-5" />
          </button>
        </div>

        {/* Field tabs (multi-field mode for new fields) */}
        {!isEdit && (
          <div className="flex items-center gap-1 border-b px-6 py-2 overflow-x-auto">
            {forms.map((f, i) => (
              <button
                key={i}
                onClick={() => setActiveIdx(i)}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  activeIdx === i
                    ? "bg-[var(--sapling-orange)] text-white"
                    : "text-muted-foreground hover:bg-gray-100"
                }`}
              >
                {f.name || `Field ${i + 1}`}
                {forms.length > 1 && (
                  <span
                    onClick={(e) => { e.stopPropagation(); removeField(i); }}
                    className="ml-1 rounded-full p-0.5 hover:bg-white/30"
                  >
                    <X className="size-3" />
                  </span>
                )}
              </button>
            ))}
            <button
              onClick={addField}
              className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-gray-100"
            >
              <Plus className="size-3" /> Add
            </button>
            <button
              onClick={() => duplicateField(activeIdx)}
              className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-gray-100"
            >
              <Copy className="size-3" /> Duplicate
            </button>
          </div>
        )}

        {/* Form content */}
        <div className="max-h-[75vh] overflow-y-auto px-6 py-5">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Left column */}
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Field Name *</Label>
                  <Input value={form.name} onChange={(e) => updateForm(activeIdx, { name: e.target.value })} placeholder="e.g. Block A" />
                </div>
                <div className="space-y-1.5">
                  <Label>Area (ha)</Label>
                  <Input type="number" step="0.1" value={form.sizeHa} onChange={(e) => updateForm(activeIdx, { sizeHa: e.target.value })} placeholder="0.0" />
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>GPS Latitude</Label>
                  <Input type="number" step="any" value={form.gpsLat} onChange={(e) => updateForm(activeIdx, { gpsLat: e.target.value })} placeholder="-25.7461" />
                </div>
                <div className="space-y-1.5">
                  <Label>GPS Longitude</Label>
                  <Input type="number" step="any" value={form.gpsLng} onChange={(e) => updateForm(activeIdx, { gpsLng: e.target.value })} placeholder="28.1881" />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Soil Type</Label>
                <select
                  value={form.soilType}
                  onChange={(e) => updateForm(activeIdx, { soilType: e.target.value })}
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                >
                  <option value="">Select soil type...</option>
                  {["Sandy", "Sandy loam", "Loam", "Silt loam", "Clay loam", "Sandy clay loam", "Sandy clay", "Silty clay", "Clay", "Peat", "Gravel"].map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Crop */}
              <div className="border-t pt-4">
                <h3 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Crop Information</h3>
                <div className="space-y-3">
                  <ComboBox
                    label="Crop"
                    placeholder="Select crop..."
                    items={crops.map((c) => ({ name: c.crop, value: c.crop }))}
                    value={form.crop}
                    onChange={(val) => handleCropSelect(activeIdx, val)}
                    onSelect={(item) => handleCropSelect(activeIdx, item.value as string)}
                  />
                  {form.cropType && (
                    <p className="text-xs">
                      Type: <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        form.cropType === "perennial" ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"
                      }`}>{form.cropType}</span>
                    </p>
                  )}
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label>Cultivar</Label>
                      <Input value={form.cultivar} onChange={(e) => updateForm(activeIdx, { cultivar: e.target.value })} placeholder="Optional" />
                    </div>
                    {form.cropType === "perennial" ? (
                      <div className="space-y-1.5">
                        <Label>Tree Age (years)</Label>
                        <Input type="number" value={form.treeAge} onChange={(e) => updateForm(activeIdx, { treeAge: e.target.value })} placeholder="0" />
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        <Label>Planting Date</Label>
                        <Input type="date" value={form.plantingDate} onChange={(e) => updateForm(activeIdx, { plantingDate: e.target.value })} />
                      </div>
                    )}
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="space-y-1.5">
                      <Label>Pop/ha</Label>
                      <Input type="number" value={form.popPerHa} onChange={(e) => updateForm(activeIdx, { popPerHa: e.target.value })} placeholder="0" />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Yield Target</Label>
                      <Input type="number" value={form.yieldTarget} onChange={(e) => updateForm(activeIdx, { yieldTarget: e.target.value })} placeholder="0" />
                      {(!form.yieldTarget || parseFloat(form.yieldTarget) === 0) && (
                        <p className="text-[11px] text-muted-foreground">
                          Leave blank or 0 — engine uses the SA full-bearing
                          potential for this crop. Tree age then scales rates
                          for young / non-bearing blocks.
                        </p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label>Unit</Label>
                      <Input value={form.yieldUnit} onChange={(e) => updateForm(activeIdx, { yieldUnit: e.target.value })} placeholder="t/ha" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right column */}
            <div className="space-y-4">
              {/* Irrigation & Methods */}
              <div>
                <h3 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Irrigation & Application Methods</h3>
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label>Irrigation Type</Label>
                    <select
                      value={form.irrigationType}
                      onChange={(e) => {
                        const val = e.target.value;
                        updateForm(activeIdx, { irrigationType: val });
                        if (val === "none" || !val) {
                          setForms((prev) => {
                            const u = [...prev];
                            u[activeIdx] = {
                              ...u[activeIdx],
                              irrigationType: val,
                              acceptedMethods: u[activeIdx].acceptedMethods.filter((m) => m !== "fertigation"),
                            };
                            return u;
                          });
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

                  <div className="space-y-1.5">
                    <Label>Accepted Methods</Label>
                    {form.cropMethods.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {form.cropMethods.map((cm) => {
                          const isChecked = form.acceptedMethods.includes(cm.method);
                          const isFertigation = cm.method === "fertigation";
                          const noIrrigation = form.irrigationType === "none" || !form.irrigationType;
                          const disabled = isFertigation && noIrrigation;
                          return (
                            <button
                              key={cm.method}
                              type="button"
                              onClick={() => !disabled && toggleMethod(activeIdx, cm.method)}
                              disabled={disabled}
                              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                                isChecked
                                  ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                                  : disabled
                                    ? "cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300"
                                    : "border-gray-200 text-gray-600 hover:border-gray-400"
                              }`}
                            >
                              {methodLabel(cm.method)}{cm.is_default && " *"}
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

                </div>
              </div>

              {/* Soil analysis */}
              {analyses.length > 0 && (
                <div className="border-t pt-4">
                  <h3 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Soil Analysis</h3>
                  <select
                    value={form.latestAnalysisId}
                    onChange={(e) => updateForm(activeIdx, { latestAnalysisId: e.target.value })}
                    className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                  >
                    <option value="">None</option>
                    {analyses.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.crop || "Unknown"} — {a.analysis_date || new Date(a.created_at).toLocaleDateString()}{a.lab_name ? ` (${a.lab_name})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t px-6 py-4">
          <p className="text-xs text-muted-foreground">
            {isEdit ? "Editing field" : `${forms.length} field${forms.length > 1 ? "s" : ""} to create`}
          </p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
              {isEdit ? "Save Changes" : `Create ${forms.length > 1 ? `${forms.length} Fields` : "Field"}`}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
