"use client";

import { Fragment, useState, useEffect, useRef } from "react";
import { API_URL, api, isFieldAnalysisConflict, type FieldAnalysisConflict } from "@/lib/api";
import { ConflictResolutionDialog, type ConflictResolutionChoice } from "@/components/conflict-resolution-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "sonner";
import {
  Loader2,
  Upload,
  PenLine,
  FileText,
  Check,
  X,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Layers,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────

interface ExtractedSample {
  sample_id?: string;
  block_name?: string;
  crop?: string;
  cultivar?: string;
  values: Record<string, number>;
}

interface FieldOption {
  id: string;
  name: string;
  crop?: string;
  cultivar?: string;
  yield_target?: number;
  yield_unit?: string;
  farm_id?: string;
  farm_name?: string;
}

interface ComponentSample {
  key: string;
  location_label: string;
  weight_ha: string;
  depth_cm: string;
  values: Record<string, string>;
}

interface SampleRow {
  key: string; // unique key for React
  field_id: string;
  field_name: string;
  /** Additional field IDs the same analysis should be cloned to on save.
   * Lets one composite/zonal sample link to several blocks in one go. */
  additional_field_ids: string[];
  crop: string;
  cultivar: string;
  yield_target: string;
  yield_unit: string;
  analysis_type: "soil" | "leaf";
  values: Record<string, string>;
  auto_matched: boolean;
  // When non-null, the row is in multi-sample mode: each component
  // carries its own lab values + optional zone metadata. The server
  // aggregates them when saving (area-weighted if every component
  // supplies a positive weight_ha, otherwise equal). Leaving this null
  // keeps the legacy single-sample flow untouched.
  components: ComponentSample[] | null;
}

interface BatchAnalysisUploadProps {
  open: boolean;
  onClose: () => void;
  clientId: string;
  clientName: string;
  farmId?: string;
  farmName?: string;
  fields: FieldOption[];
  onSaved: () => void;
}

const SOIL_PARAMS = [
  "pH (H2O)", "pH (KCl)", "Org C", "CEC", "Clay",
  "N (total)", "P (Bray-1)", "K", "Ca", "Mg", "S",
  "Fe", "B", "Mn", "Zn", "Mo", "Cu", "Na",
];

const LEAF_PARAMS = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu", "B", "Mo"];

// ── Component ─────────────────────────────────────────────────────────

export function BatchAnalysisUpload({
  open,
  onClose,
  clientId,
  clientName,
  farmId,
  farmName,
  fields,
  onSaved,
}: BatchAnalysisUploadProps) {
  const [mode, setMode] = useState<"choose" | "upload" | "manual" | "review">("choose");
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [labName, setLabName] = useState("");
  const [analysisDate, setAnalysisDate] = useState("");
  const [analysisType, setAnalysisType] = useState<"soil" | "leaf">("soil");
  const [rows, setRows] = useState<SampleRow[]>([]);
  const [sourceDocumentUrl, setSourceDocumentUrl] = useState<string | null>(null);
  const [localFields, setLocalFields] = useState<FieldOption[]>(fields);
  const [pendingConflicts, setPendingConflicts] = useState<FieldAnalysisConflict[]>([]);
  const pendingPayloadRef = useRef<Record<string, unknown> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const moreFileInputRef = useRef<HTMLInputElement>(null);

  // Sync local fields with prop changes
  useEffect(() => { setLocalFields(fields); }, [fields]);

  // Reset when sheet opens/closes
  useEffect(() => {
    if (open) {
      setMode("choose");
      setRows([]);
      setLabName("");
      setAnalysisDate("");
      setAnalysisType("soil");
      setLocalFields(fields);
    }
  }, [open]);

  // ── Upload & extraction ─────────────────────────────────────────────

  const handleFileUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setExtracting(true);

    for (const file of Array.from(fileList)) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        if (labName) formData.append("lab_name_hint", labName);
        if (clientId) formData.append("client_id", clientId);

        const token = (
          await (await import("@/lib/supabase")).createClient().auth.getSession()
        ).data.session?.access_token;
        const res = await fetch(`${API_URL}/api/soil/extract`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          const detail = (body as { detail?: string }).detail;
          toast.error(
            `Failed to extract ${file.name}: ${detail || `HTTP ${res.status}`}`,
            { duration: 10000 },
          );
          continue;
        }

        const data = await res.json();
        const samples: ExtractedSample[] = data.samples || [];
        const detectedLab = data.lab_name || data.labName;
        const detectedDate = data.analysis_date || data.analysisDate;
        const department = (data.department || "").toLowerCase();
        const isLeaf = department.includes("leaf");

        if (detectedLab && !labName) setLabName(detectedLab);
        if (detectedDate && !analysisDate) setAnalysisDate(detectedDate);
        if (isLeaf) setAnalysisType("leaf");
        if (data.source_document_url) setSourceDocumentUrl(data.source_document_url);

        // Filter out norm/reference rows
        const realSamples = samples.filter((s) => {
          const name = (s.block_name || s.sample_id || "").toLowerCase();
          return !name.includes("norm") && !name.includes("reference") && !name.includes("standard");
        });

        // Convert extracted samples to rows, auto-matching to fields
        const newRows: SampleRow[] = realSamples.map((s, i) => {
          const sampleName = s.block_name || s.sample_id || `Sample ${i + 1}`;
          // Auto-match: try exact, then partial (field name ends with sample name)
          const match = localFields.find((f) => {
            const fn = f.name.toLowerCase();
            const sn = sampleName.toLowerCase();
            return fn === sn || fn.endsWith(sn) || fn.includes(sn);
          });

          // Normalize extracted value keys to standard param names
          const mappedValues: Record<string, string> = {};
          const paramList = isLeaf ? LEAF_PARAMS : SOIL_PARAMS;
          const usedKeys = new Set<string>();
          for (const param of paramList) {
            const paramLower = param.toLowerCase();
            const pWords = paramLower.split(/[^a-z0-9]+/).filter(Boolean);
            const entry = Object.entries(s.values).find(([k]) => {
              if (usedKeys.has(k)) return false;
              const kl = k.toLowerCase();
              if (kl === paramLower) return true;
              // Get the element symbol from the key (first word, or second if first is "total")
              const kWords = kl.split(/[^a-z0-9]+/).filter(Boolean);
              let kElem = kWords[0];
              if (kElem === "total" && kWords.length > 1) kElem = kWords[1];
              return kElem === pWords[0];
            });
            if (entry && entry[1] != null) {
              mappedValues[param] = String(entry[1]);
              usedKeys.add(entry[0]);
            }
          }

          return {
            key: `${Date.now()}-${i}`,
            field_id: match?.id || "",
            field_name: match?.name || sampleName,
            additional_field_ids: [],
            crop: s.crop || match?.crop || "",
            cultivar: s.cultivar || match?.cultivar || "",
            yield_target: match?.yield_target ? String(match.yield_target) : "",
            yield_unit: match?.yield_unit || "",
            analysis_type: isLeaf ? "leaf" : "soil",
            values: mappedValues,
            auto_matched: !!match,
            components: null,
          };
        });

        setRows((prev) => [...prev, ...newRows]);
        toast.success(`Extracted ${samples.length} sample${samples.length !== 1 ? "s" : ""} from ${file.name}`);
      } catch (err) {
        console.error(`batch extract failed for ${file.name}`, err);
        const msg = err instanceof Error ? err.message : "unknown error";
        toast.error(`Error processing ${file.name}: ${msg}`, { duration: 10000 });
      }
    }

    setExtracting(false);
    setMode("review");
  };

  // ── Manual entry ────────────────────────────────────────────────────

  const addManualRow = () => {
    setRows((prev) => [
      ...prev,
      {
        key: `manual-${Date.now()}`,
        field_id: "",
        field_name: "",
        additional_field_ids: [],
        crop: "",
        cultivar: "",
        yield_target: "",
        yield_unit: "",
        analysis_type: analysisType,
        values: {},
        auto_matched: false,
        components: null,
      },
    ]);
  };

  const startManual = () => {
    setMode("review");
    addManualRow();
  };

  // ── Row editing ─────────────────────────────────────────────────────

  const updateRow = (key: string, updates: Partial<SampleRow>) => {
    setRows((prev) =>
      prev.map((r) => (r.key === key ? { ...r, ...updates } : r))
    );
  };

  const removeRow = (key: string) => {
    setRows((prev) => prev.filter((r) => r.key !== key));
  };

  // ── Multi-sample (component) editing ────────────────────────────────

  const makeComponentKey = () => `comp-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

  /**
   * Toggle a row between single-sample and multi-sample mode.
   *
   * Enter multi-sample: the row's current values become the first
   * component (so nothing is lost) and a blank second component is
   * added so the user can start entering zone 2 immediately.
   *
   * Exit multi-sample: only allowed when <=1 components exist. Values
   * from component 0 (if present) fold back into the row. This keeps
   * the collapse button from silently discarding zone data.
   */
  const toggleMultiSample = (key: string) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.key !== key) return r;
        if (r.components == null) {
          return {
            ...r,
            components: [
              {
                key: makeComponentKey(),
                location_label: "",
                weight_ha: "",
                depth_cm: "",
                values: { ...r.values },
              },
              {
                key: makeComponentKey(),
                location_label: "",
                weight_ha: "",
                depth_cm: "",
                values: {},
              },
            ],
          };
        }
        if (r.components.length > 1) return r;  // cannot collapse with multiple zones
        return {
          ...r,
          values: r.components[0]?.values ?? {},
          components: null,
        };
      })
    );
  };

  const addComponent = (rowKey: string) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.key !== rowKey || r.components == null) return r;
        return {
          ...r,
          components: [
            ...r.components,
            {
              key: makeComponentKey(),
              location_label: "",
              weight_ha: "",
              depth_cm: "",
              values: {},
            },
          ],
        };
      })
    );
  };

  const updateComponent = (
    rowKey: string,
    compKey: string,
    patch: Partial<ComponentSample>,
  ) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.key !== rowKey || r.components == null) return r;
        return {
          ...r,
          components: r.components.map((c) =>
            c.key === compKey ? { ...c, ...patch } : c,
          ),
        };
      })
    );
  };

  const removeComponent = (rowKey: string, compKey: string) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.key !== rowKey || r.components == null) return r;
        const next = r.components.filter((c) => c.key !== compKey);
        return { ...r, components: next };
      })
    );
  };

  const selectField = (key: string, fieldId: string) => {
    const field = localFields.find((f) => f.id === fieldId);
    if (field) {
      updateRow(key, {
        field_id: field.id,
        field_name: field.name,
        crop: field.crop || "",
        cultivar: field.cultivar || "",
        yield_target: field.yield_target ? String(field.yield_target) : "",
        yield_unit: field.yield_unit || "",
      });
    }
  };

  const createFieldForRow = async (rowKey: string) => {
    const row = rows.find((r) => r.key === rowKey);
    if (!row) return;

    // Need a farm to create the field under — use the first farm available
    const farmIds = [...new Set(localFields.map((f) => f.farm_id).filter(Boolean))];
    if (farmIds.length === 0) {
      toast.error("No farms available — add a farm first");
      return;
    }

    // If multiple farms, pick the one that has most fields (or first)
    const targetFarmId = farmIds[0];
    const targetFarm = localFields.find((f) => f.farm_id === targetFarmId);

    try {
      const newField = await api.post<{ id: string; name: string }>(`/api/clients/farms/${targetFarmId}/fields`, {
        name: row.field_name || `Block ${rows.indexOf(row) + 1}`,
        crop: row.crop || undefined,
        cultivar: row.cultivar || undefined,
      });

      // Add to local fields list
      const fieldOption: FieldOption = {
        id: newField.id,
        name: newField.name,
        crop: row.crop || undefined,
        cultivar: row.cultivar || undefined,
        farm_id: targetFarmId,
        farm_name: targetFarm?.farm_name || "",
      };
      setLocalFields((prev) => [...prev, fieldOption]);

      // Link row to the new field
      updateRow(rowKey, { field_id: newField.id, field_name: newField.name });
      toast.success(`Created field "${newField.name}"`);
    } catch {
      toast.error("Failed to create field");
    }
  };

  // ── Save all ────────────────────────────────────────────────────────

  const handleSave = async () => {
    const hasAnyValue = (vals: Record<string, string>) =>
      Object.values(vals).some((v) => v && v !== "0");

    const rowHasData = (r: SampleRow) => {
      if (r.components && r.components.length > 0) {
        return r.components.some((c) => hasAnyValue(c.values));
      }
      return hasAnyValue(r.values);
    };

    const validRows = rows.filter(rowHasData);

    if (validRows.length === 0) {
      toast.error("No samples with values to save");
      return;
    }

    setSaving(true);
    try {
      const items = validRows.flatMap((r) => {
        const toNumericValues = (vals: Record<string, string>) => {
          const out: Record<string, number | null> = {};
          for (const [k, v] of Object.entries(vals)) {
            const n = parseFloat(v);
            out[k] = isNaN(n) ? null : n;
          }
          return out;
        };

        // Multi-sample mode: only send component_samples when the user
        // actually entered ≥2 zones with data. A single filled component
        // is treated as a plain single-sample record at the server.
        const filledComponents =
          r.components?.filter((c) => hasAnyValue(c.values)) ?? [];

        // Resolve which fields this analysis links to. Empty primary +
        // additionals → one unlinked row. Otherwise: primary first, then
        // each additional (with the same values, distinct field_id).
        const fieldsToWrite: Array<{ id: string | null; name: string | null }> = [];
        const seen = new Set<string>();
        const pushField = (id: string) => {
          if (!id || seen.has(id)) return;
          seen.add(id);
          const f = localFields.find((lf) => lf.id === id);
          fieldsToWrite.push({ id, name: f?.name ?? null });
        };
        if (r.field_id) pushField(r.field_id);
        for (const fid of r.additional_field_ids ?? []) pushField(fid);
        if (fieldsToWrite.length === 0) {
          fieldsToWrite.push({ id: null, name: r.field_name || null });
        }

        if (filledComponents.length >= 2) {
          return fieldsToWrite.map((f) => ({
            field_id: f.id,
            field_name: f.name,
            crop: r.crop || null,
            cultivar: r.cultivar || null,
            yield_target: r.yield_target ? parseFloat(r.yield_target) : null,
            yield_unit: r.yield_unit || null,
            analysis_type: r.analysis_type,
            soil_values: toNumericValues(filledComponents[0].values),
            component_samples: filledComponents.map((c) => ({
              values: toNumericValues(c.values),
              weight_ha: c.weight_ha ? parseFloat(c.weight_ha) : null,
              location_label: c.location_label || null,
              depth_cm: c.depth_cm ? parseFloat(c.depth_cm) : null,
            })),
          }));
        }

        const baseValues = filledComponents[0]?.values ?? r.values;
        return fieldsToWrite.map((f) => ({
          field_id: f.id,
          field_name: f.name,
          crop: r.crop || null,
          cultivar: r.cultivar || null,
          yield_target: r.yield_target ? parseFloat(r.yield_target) : null,
          yield_unit: r.yield_unit || null,
          analysis_type: r.analysis_type,
          soil_values: toNumericValues(baseValues),
        }));
      });

      const basePayload = {
        client_id: clientId,
        farm_id: farmId || null,
        lab_name: labName || null,
        analysis_date: analysisDate || null,
        source_document_url: sourceDocumentUrl || null,
        items,
      };

      try {
        const res = await api.post<{ saved: number; analyses: unknown[] }>("/api/soil/batch", basePayload);
        toast.success(`Saved ${res.saved} analyse${res.saved !== 1 ? "s" : ""}`);
        onSaved();
        onClose();
      } catch (err) {
        const conflicts = isFieldAnalysisConflict(err);
        if (!conflicts) throw err;
        // Defer to the conflict dialog — the user picks a resolution and
        // handleConflictResolved re-posts with the chosen flag.
        pendingPayloadRef.current = basePayload;
        setPendingConflicts(conflicts);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save", {
        duration: 10000,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleConflictResolved = async (choice: ConflictResolutionChoice) => {
    const payload = pendingPayloadRef.current;
    if (!payload) {
      setPendingConflicts([]);
      return;
    }
    setPendingConflicts([]);
    setSaving(true);
    try {
      const res = await api.post<{ saved: number; analyses: unknown[] }>("/api/soil/batch", {
        ...payload,
        conflict_resolution: choice,
      });
      const verb = choice === "merge_as_composite" ? "Merged" : "Saved";
      toast.success(`${verb} ${res.saved} analyse${res.saved !== 1 ? "s" : ""}`);
      onSaved();
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save", {
        duration: 10000,
      });
    } finally {
      setSaving(false);
      pendingPayloadRef.current = null;
    }
  };

  const handleConflictCancelled = () => {
    setPendingConflicts([]);
    pendingPayloadRef.current = null;
    toast.info("Save cancelled — no changes made");
  };

  // ── Render ──────────────────────────────────────────────────────────

  const params = analysisType === "leaf" ? LEAF_PARAMS : SOIL_PARAMS;
  const matchedCount = rows.filter((r) => r.field_id).length;
  const unmatchedCount = rows.filter((r) => !r.field_id).length;

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="bottom" className="flex h-[90vh] flex-col overflow-hidden">
        <SheetHeader>
          <SheetTitle>
            Upload Lab Results {farmName ? `- ${farmName}` : `- ${clientName}`}
          </SheetTitle>
        </SheetHeader>

        <div className="flex-1 space-y-6 overflow-y-auto">
          {/* Mode selection */}
          {mode === "choose" && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Upload a lab report PDF or enter values manually for each block.
              </p>

              {/* Lab info */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label>Lab Name</Label>
                  <Input
                    value={labName}
                    onChange={(e) => setLabName(e.target.value)}
                    placeholder="e.g. NviroTek"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Analysis Date</Label>
                  <Input
                    type="date"
                    value={analysisDate}
                    onChange={(e) => setAnalysisDate(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <div className="flex gap-1 rounded-lg bg-muted p-1">
                    {(["soil", "leaf"] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setAnalysisType(t)}
                        className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                          analysisType === t
                            ? "bg-white text-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {t === "soil" ? "Soil" : "Leaf"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp"
                multiple
                className="hidden"
                onChange={(e) => {
                  setMode("upload");
                  handleFileUpload(e.target.files);
                  e.target.value = "";
                }}
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center gap-3 rounded-xl border-2 border-dashed border-muted-foreground/25 p-8 text-center transition-colors hover:border-[var(--sapling-orange)] hover:bg-orange-50/50"
                >
                  <Upload className="size-8 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Upload Lab Report</p>
                    <p className="text-xs text-muted-foreground">PDF or image — AI extracts all samples</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={startManual}
                  className="flex flex-col items-center gap-3 rounded-xl border-2 border-dashed border-muted-foreground/25 p-8 text-center transition-colors hover:border-[var(--sapling-orange)] hover:bg-orange-50/50"
                >
                  <PenLine className="size-8 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Enter Manually</p>
                    <p className="text-xs text-muted-foreground">Type values for each block</p>
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* Extracting state */}
          {mode === "upload" && extracting && (
            <div className="flex flex-col items-center gap-3 py-12">
              <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
              <p className="text-sm text-muted-foreground">Extracting samples from lab report...</p>
            </div>
          )}

          {/* Review / edit rows — spreadsheet table */}
          {mode === "review" && (
            <div className="flex flex-1 flex-col gap-3 overflow-hidden">
              {/* Top bar: summary + lab info + actions */}
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm font-medium">{rows.length} sample{rows.length !== 1 ? "s" : ""}</span>
                {matchedCount > 0 && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    {matchedCount} matched
                  </span>
                )}
                {unmatchedCount > 0 && (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                    {unmatchedCount} unmatched
                  </span>
                )}
                <div className="flex items-center gap-2">
                  <Input value={labName} onChange={(e) => setLabName(e.target.value)} placeholder="Lab Name" className="h-7 w-28 text-xs" />
                  <Input type="date" value={analysisDate} onChange={(e) => setAnalysisDate(e.target.value)} className="h-7 w-32 text-xs" />
                </div>
                <div className="flex-1" />
                <Button size="sm" variant="outline" onClick={addManualRow}>
                  <Plus className="size-3" /> Add Row
                </Button>
                <input ref={moreFileInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" multiple className="hidden"
                  onChange={(e) => { setExtracting(true); handleFileUpload(e.target.files).finally(() => setExtracting(false)); e.target.value = ""; }}
                />
                <Button size="sm" variant="outline" onClick={() => moreFileInputRef.current?.click()}>
                  <Upload className="size-3" /> Upload More
                </Button>
              </div>

              {/* Scrollable table */}
              <div className="flex-1 overflow-auto rounded-lg border">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 z-10 bg-gray-50">
                    <tr className="border-b text-left">
                      <th className="whitespace-nowrap px-2 py-1.5 font-medium text-muted-foreground">Sample</th>
                      <th className="whitespace-nowrap px-2 py-1.5 font-medium text-muted-foreground">Field / Block</th>
                      <th className="whitespace-nowrap px-2 py-1.5 font-medium text-muted-foreground">Crop</th>
                      <th className="whitespace-nowrap px-2 py-1.5 font-medium text-muted-foreground">Cultivar</th>
                      {params.map((p) => (
                        <th key={p} className="whitespace-nowrap px-1 py-1.5 text-center font-medium text-muted-foreground">{p}</th>
                      ))}
                      <th className="px-1 py-1.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => {
                      const isMulti = row.components !== null;
                      const canCollapse = isMulti && (row.components?.length ?? 0) <= 1;
                      return (
                      <Fragment key={row.key}>
                      <tr
                        className={`border-b last:border-0 ${
                          row.field_id ? "bg-white" : "bg-amber-50"
                        }`}
                      >
                        <td className="whitespace-nowrap px-2 py-1">
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => toggleMultiSample(row.key)}
                              disabled={isMulti && !canCollapse}
                              title={
                                isMulti
                                  ? canCollapse
                                    ? "Collapse to single sample"
                                    : "Remove extra zones first"
                                  : "Split into zone samples"
                              }
                              className={`flex size-5 items-center justify-center rounded hover:bg-muted ${
                                isMulti ? "text-[var(--sapling-orange)]" : "text-muted-foreground"
                              } disabled:opacity-40`}
                            >
                              {isMulti ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
                            </button>
                            <span className="font-medium">{row.field_name || "—"}</span>
                            {isMulti && (
                              <span className="inline-flex items-center gap-0.5 rounded-full bg-orange-100 px-1.5 py-0.5 text-[10px] font-medium text-orange-700">
                                <Layers className="size-2.5" />
                                {row.components?.length ?? 0}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-2 py-1">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-0.5">
                              <select
                                value={row.field_id}
                                onChange={(e) => selectField(row.key, e.target.value)}
                                className="h-6 w-36 rounded border bg-transparent px-1 text-xs"
                              >
                                <option value="">Select...</option>
                                {localFields.map((f) => (
                                  <option key={f.id} value={f.id}>
                                    {f.farm_name ? `${f.farm_name} / ` : ""}{f.name}
                                  </option>
                                ))}
                              </select>
                              {!row.field_id && (
                                <button onClick={() => createFieldForRow(row.key)} className="text-[var(--sapling-orange)]" title="Create field">
                                  <Plus className="size-3" />
                                </button>
                              )}
                            </div>
                            {row.field_id && (
                              <AdditionalFieldsPicker
                                row={row}
                                allFields={localFields}
                                onChange={(ids) =>
                                  updateRow(row.key, { additional_field_ids: ids })
                                }
                              />
                            )}
                          </div>
                        </td>
                        <td className="px-2 py-1">
                          <input
                            value={row.crop}
                            onChange={(e) => updateRow(row.key, { crop: e.target.value })}
                            className="h-6 w-20 rounded border px-1 text-xs"
                            placeholder="Crop"
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            value={row.cultivar}
                            onChange={(e) => updateRow(row.key, { cultivar: e.target.value })}
                            className="h-6 w-24 rounded border px-1 text-xs"
                            placeholder="Cultivar"
                          />
                        </td>
                        {params.map((p) => (
                          <td key={p} className="px-0.5 py-1">
                            {isMulti ? (
                              <div
                                className="flex h-6 w-14 items-center justify-center rounded border border-dashed border-muted-foreground/30 bg-muted/40 text-center text-[10px] italic tabular-nums text-muted-foreground"
                                title="Values entered per zone below; server aggregates on save"
                              >
                                mean
                              </div>
                            ) : (
                              <input
                                type="number"
                                step="any"
                                value={row.values[p] || ""}
                                onChange={(e) =>
                                  updateRow(row.key, { values: { ...row.values, [p]: e.target.value } })
                                }
                                className="h-6 w-14 rounded border px-1 text-center text-xs tabular-nums"
                                placeholder="—"
                              />
                            )}
                          </td>
                        ))}
                        <td className="px-1 py-1">
                          <button onClick={() => removeRow(row.key)} className="text-muted-foreground hover:text-red-500">
                            <X className="size-3" />
                          </button>
                        </td>
                      </tr>
                      {isMulti && row.components && (
                        <tr className="bg-orange-50/30">
                          <td colSpan={params.length + 5} className="px-3 py-2">
                            <div className="space-y-1.5">
                              <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                                <Layers className="size-3" />
                                <span>
                                  Zone samples — the server will area-weight if every zone has a hectare weight, otherwise equal weights.
                                </span>
                              </div>
                              {row.components.map((comp, idx) => {
                                const componentsCount = row.components!.length;
                                return (
                                  <div key={comp.key} className="flex flex-wrap items-center gap-1.5 rounded border border-orange-200/70 bg-white px-2 py-1.5">
                                    <span className="w-14 shrink-0 text-[10px] font-medium text-muted-foreground">
                                      Zone {idx + 1}
                                    </span>
                                    <input
                                      value={comp.location_label}
                                      onChange={(e) => updateComponent(row.key, comp.key, { location_label: e.target.value })}
                                      placeholder="Label (e.g. North)"
                                      className="h-6 w-28 rounded border px-1 text-xs"
                                    />
                                    <input
                                      type="number"
                                      step="any"
                                      value={comp.weight_ha}
                                      onChange={(e) => updateComponent(row.key, comp.key, { weight_ha: e.target.value })}
                                      placeholder="ha"
                                      className="h-6 w-14 rounded border px-1 text-center text-xs tabular-nums"
                                      title="Zone area in hectares (optional, enables area-weighted mean)"
                                    />
                                    <input
                                      type="number"
                                      step="any"
                                      value={comp.depth_cm}
                                      onChange={(e) => updateComponent(row.key, comp.key, { depth_cm: e.target.value })}
                                      placeholder="cm"
                                      className="h-6 w-12 rounded border px-1 text-center text-xs tabular-nums"
                                      title="Sampling depth (optional)"
                                    />
                                    <div className="flex flex-wrap items-center gap-0.5">
                                      {params.map((p) => (
                                        <div key={p} className="flex flex-col items-center">
                                          <span className="text-[9px] text-muted-foreground">{p}</span>
                                          <input
                                            type="number"
                                            step="any"
                                            value={comp.values[p] || ""}
                                            onChange={(e) =>
                                              updateComponent(row.key, comp.key, {
                                                values: { ...comp.values, [p]: e.target.value },
                                              })
                                            }
                                            className="h-6 w-12 rounded border px-1 text-center text-xs tabular-nums"
                                            placeholder="—"
                                          />
                                        </div>
                                      ))}
                                    </div>
                                    <div className="flex-1" />
                                    <button
                                      type="button"
                                      onClick={() => removeComponent(row.key, comp.key)}
                                      disabled={componentsCount <= 1}
                                      className="text-muted-foreground hover:text-red-500 disabled:opacity-30"
                                      title={componentsCount <= 1 ? "At least one zone required" : "Remove zone"}
                                    >
                                      <X className="size-3" />
                                    </button>
                                  </div>
                                );
                              })}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => addComponent(row.key)}
                                className="h-7 text-xs"
                              >
                                <Plus className="size-3" /> Add zone sample
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )}
                      </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Bottom actions */}
              <div className="flex items-center gap-3 border-t pt-3">
                <Button variant="outline" onClick={() => { setMode("choose"); setRows([]); }}>
                  Back
                </Button>
                <div className="flex-1" />
                <Button
                  onClick={handleSave}
                  disabled={saving || rows.length === 0}
                  className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  {saving ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
                  Save {rows.length} Analyse{rows.length !== 1 ? "s" : ""}
                </Button>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
      <ConflictResolutionDialog
        open={pendingConflicts.length > 0}
        conflicts={pendingConflicts}
        onResolve={handleConflictResolved}
        onCancel={handleConflictCancelled}
      />
    </Sheet>
  );
}

/** Sub-row picker that lets the agronomist clone the same analysis to
 * additional blocks at save time — composite samples often represent
 * several blocks at once. The primary field stays in row.field_id;
 * extras land in row.additional_field_ids and the save flow expands
 * them into one soil_analyses row per linked field. */
function AdditionalFieldsPicker({
  row,
  allFields,
  onChange,
}: {
  row: SampleRow;
  allFields: FieldOption[];
  onChange: (ids: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const candidates = allFields.filter((f) => f.id !== row.field_id);
  if (candidates.length === 0) return null;
  const selected = new Set(row.additional_field_ids ?? []);
  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(Array.from(next));
  };
  return (
    <div className="flex flex-col items-start">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-[10px] text-muted-foreground hover:text-[var(--sapling-orange)]"
      >
        + also apply to {selected.size > 0 ? `${selected.size} more` : "other blocks"}
      </button>
      {open && (
        <div className="mt-1 max-h-40 w-44 overflow-y-auto rounded border bg-white p-1 shadow-sm">
          {candidates.map((f) => (
            <label
              key={f.id}
              className="flex cursor-pointer items-center gap-1.5 rounded px-1.5 py-1 text-[11px] hover:bg-orange-50"
            >
              <input
                type="checkbox"
                checked={selected.has(f.id)}
                onChange={() => toggle(f.id)}
                className="size-3 accent-[var(--sapling-orange)]"
              />
              <span className="truncate">
                {f.farm_name ? `${f.farm_name} / ` : ""}
                {f.name}
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
