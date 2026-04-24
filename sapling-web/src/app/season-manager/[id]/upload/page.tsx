"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { api, API_URL } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Upload,
  FileText,
  PenLine,
  Loader2,
  ChevronLeft,
  Check,
  AlertTriangle,
  Trash2,
  Save,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────

interface Block {
  id: string;
  name: string;
  crop: string;
  cultivar: string | null;
  area_ha: number | null;
}

interface SampleRow {
  id: string; // temp client ID
  block_id: string;
  block_name: string;
  crop: string;
  cultivar: string;
  sample_id: string;
  values: Record<string, string>;
  include: boolean;
  auto_matched: boolean;
  outlier_keys: string[];
}

// ── Helpers ──────────────────────────────────────────────────────────

let _nextId = 0;
function tempId() { return `temp-${++_nextId}`; }

const VALUE_KEYS = ["N", "P", "K", "Ca", "Mg", "Na", "Mn", "Fe", "Cu", "Zn", "B"];

function emptyRow(blocks: Block[]): SampleRow {
  return {
    id: tempId(),
    block_id: "",
    block_name: "",
    crop: "",
    cultivar: "",
    sample_id: "",
    values: {},
    include: true,
    auto_matched: false,
    outlier_keys: [],
  };
}

// ── Component ──────────────────────────────────────────────────────────

export default function BulkUploadPage() {
  const params = useParams();
  const router = useRouter();
  const programmeId = params.id as string;

  const [blocks, setBlocks] = useState<Block[]>([]);
  const [programmeName, setProgrammeName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Input mode
  const [mode, setMode] = useState<"choose" | "manual" | "upload">("choose");
  const [extracting, setExtracting] = useState(false);

  // Analysis type detected from report
  const [analysisType, setAnalysisType] = useState<"soil" | "leaf">("leaf");
  const [labName, setLabName] = useState("");
  const [analysisDate, setAnalysisDate] = useState("");

  // Rows
  const [rows, setRows] = useState<SampleRow[]>([]);

  // Load programme and blocks
  useEffect(() => {
    api.get<{ name: string; blocks: Block[] }>(`/api/programmes/${programmeId}`)
      .then((prog) => {
        setProgrammeName(prog.name);
        setBlocks(prog.blocks || []);
      })
      .catch(() => {
        toast.error("Failed to load programme");
        router.push("/season-manager");
      })
      .finally(() => setLoading(false));
  }, [programmeId]);

  // Upload handler
  const handleFileUpload = async (file: File) => {
    setExtracting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const token = (await (await import("@/lib/supabase")).createClient().auth.getSession()).data.session?.access_token;
      const res = await fetch(`${API_URL}/api/soil/extract`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
        throw new Error(err.detail || `Extraction failed`);
      }
      const data = await res.json();

      if (data.lab_name) setLabName(data.lab_name);
      if (data.analysis_date) setAnalysisDate(data.analysis_date);
      if (data.department?.toLowerCase().includes("leaf")) {
        setAnalysisType("leaf");
        toast.info("Leaf analysis detected");
      } else if (data.department?.toLowerCase().includes("soil")) {
        setAnalysisType("soil");
        toast.info("Soil analysis detected");
      }

      const samples = data.samples || [];
      if (samples.length === 0) {
        toast.error("No samples found in the document");
        return;
      }

      // Filter out norm rows
      const dataSamples = samples.filter(
        (s: Record<string, unknown>) => !(s.block_name as string)?.toLowerCase().startsWith("norm")
      );

      // Convert to rows with auto-matching
      const newRows: SampleRow[] = dataSamples.map((s: Record<string, unknown>) => {
        const blockName = (s.block_name as string) || "";
        const crop = (s.crop as string) || "";
        const cultivar = (s.cultivar as string) || "";
        const sampleId = (s.sample_id as string) || "";
        const values = (s.values || {}) as Record<string, number>;

        // Try to match to a programme block by name
        const matchedBlock = blocks.find(
          (b) => b.name.toLowerCase() === blockName.toLowerCase() ||
                 blockName.toLowerCase().includes(b.name.toLowerCase()) ||
                 b.name.toLowerCase().includes(blockName.toLowerCase())
        );

        const stringValues: Record<string, string> = {};
        for (const [k, v] of Object.entries(values)) {
          if (v != null) stringValues[k] = String(v);
        }

        return {
          id: tempId(),
          block_id: matchedBlock?.id || "",
          block_name: blockName,
          crop: matchedBlock?.crop || crop,
          cultivar: matchedBlock?.cultivar || cultivar,
          sample_id: sampleId,
          values: stringValues,
          include: true,
          auto_matched: !!matchedBlock,
          outlier_keys: [],
        };
      });

      setRows(newRows);
      setMode("upload");
      toast.success(`Extracted ${newRows.length} samples`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Extraction failed", {
        duration: 10000,
      });
    } finally {
      setExtracting(false);
    }
  };

  // Add manual row
  const addRow = () => setRows((prev) => [...prev, emptyRow(blocks)]);

  // Update a row
  const updateRow = (id: string, updates: Partial<SampleRow>) => {
    setRows((prev) => prev.map((r) => r.id === id ? { ...r, ...updates } : r));
  };

  // Update a row's value
  const updateValue = (id: string, key: string, val: string) => {
    setRows((prev) => prev.map((r) =>
      r.id === id ? { ...r, values: { ...r.values, [key]: val } } : r
    ));
  };

  // Handle block selection — auto-fill crop/cultivar
  const handleBlockSelect = (rowId: string, blockId: string) => {
    const block = blocks.find((b) => b.id === blockId);
    updateRow(rowId, {
      block_id: blockId,
      block_name: block?.name || "",
      crop: block?.crop || "",
      cultivar: block?.cultivar || "",
    });
  };

  // Save all
  const handleSaveAll = async () => {
    const included = rows.filter((r) => r.include);
    if (included.length === 0) {
      toast.error("No analyses selected");
      return;
    }

    setSaving(true);
    try {
      const result = await api.post<{ saved: number }>(`/api/programmes/${programmeId}/bulk-analyses`, {
        lab_name: labName || null,
        analysis_date: analysisDate || null,
        average_same_block: true,
        analyses: included.map((r) => ({
          block_id: r.block_id || null,
          block_name: r.block_name || null,
          crop: r.crop || null,
          cultivar: r.cultivar || null,
          sample_id: r.sample_id || null,
          analysis_type: analysisType,
          values: Object.fromEntries(
            Object.entries(r.values)
              .filter(([, v]) => v && parseFloat(v) > 0)
              .map(([k, v]) => [k, parseFloat(v)])
          ),
          include: true,
        })),
      });

      toast.success(`Saved ${result.saved} analyses`);
      router.push(`/season-manager/${programmeId}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed", {
        duration: 10000,
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex min-h-[400px] items-center justify-center">
          <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-4 py-8">
        {/* Header */}
        <Button variant="ghost" size="sm" onClick={() => router.push(`/season-manager/${programmeId}`)} className="mb-3">
          <ChevronLeft className="size-4" /> Back to {programmeName}
        </Button>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Add Lab Results</h1>
          <p className="text-sm text-[var(--sapling-medium-grey)]">
            Upload a lab report or enter results manually — link each sample to a programme block
          </p>
        </div>

        {/* Mode chooser */}
        {mode === "choose" && (
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Upload option */}
            <Card
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => document.getElementById("file-input")?.click()}
            >
              <CardContent className="flex flex-col items-center gap-4 py-10">
                {extracting ? (
                  <>
                    <Loader2 className="size-10 animate-spin text-[var(--sapling-orange)]" />
                    <p className="font-medium">Reading lab report...</p>
                  </>
                ) : (
                  <>
                    <Upload className="size-10 text-[var(--sapling-orange)]" />
                    <div className="text-center">
                      <p className="font-medium text-[var(--sapling-dark)]">Upload Lab Report</p>
                      <p className="mt-1 text-sm text-muted-foreground">PDF or photo — AI extracts all samples</p>
                    </div>
                  </>
                )}
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFileUpload(file);
                    e.target.value = "";
                  }}
                />
              </CardContent>
            </Card>

            {/* Manual option */}
            <Card
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => {
                setRows(blocks.map((b) => ({
                  id: tempId(),
                  block_id: b.id,
                  block_name: b.name,
                  crop: b.crop,
                  cultivar: b.cultivar || "",
                  sample_id: "",
                  values: {},
                  include: true,
                  auto_matched: true,
                  outlier_keys: [],
                })));
                setMode("manual");
              }}
            >
              <CardContent className="flex flex-col items-center gap-4 py-10">
                <PenLine className="size-10 text-[var(--sapling-orange)]" />
                <div className="text-center">
                  <p className="font-medium text-[var(--sapling-dark)]">Enter Manually</p>
                  <p className="mt-1 text-sm text-muted-foreground">One row per block — type values directly</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Review Table */}
        {(mode === "upload" || mode === "manual") && rows.length > 0 && (
          <div className="space-y-4">
            {/* Lab info */}
            <Card>
              <CardContent className="flex flex-wrap gap-4 py-4">
                <div className="space-y-1">
                  <Label>Lab Name</Label>
                  <Input value={labName} onChange={(e) => setLabName(e.target.value)} placeholder="e.g. Bemlab" className="w-40" />
                </div>
                <div className="space-y-1">
                  <Label>Date</Label>
                  <Input type="date" value={analysisDate} onChange={(e) => setAnalysisDate(e.target.value)} className="w-40" />
                </div>
                <div className="space-y-1">
                  <Label>Type</Label>
                  <select
                    value={analysisType}
                    onChange={(e) => setAnalysisType(e.target.value as "soil" | "leaf")}
                    className="rounded-md border bg-white px-3 py-2 text-sm"
                  >
                    <option value="soil">Soil Analysis</option>
                    <option value="leaf">Leaf Analysis</option>
                  </select>
                </div>
              </CardContent>
            </Card>

            {/* Samples table */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{rows.filter((r) => r.include).length} of {rows.length} samples selected</CardTitle>
                  <Button variant="outline" size="sm" onClick={addRow}>
                    + Add Row
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="w-8 pb-2"></th>
                        <th className="pb-2 pr-2 font-medium text-muted-foreground">Block</th>
                        <th className="pb-2 pr-2 font-medium text-muted-foreground">Crop</th>
                        <th className="pb-2 pr-2 font-medium text-muted-foreground">Cultivar</th>
                        {VALUE_KEYS.map((k) => (
                          <th key={k} className="pb-2 pr-1 text-right font-medium text-muted-foreground">{k}</th>
                        ))}
                        <th className="w-8 pb-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr key={row.id} className={`border-b border-muted last:border-0 ${!row.include ? "opacity-40" : ""}`}>
                          <td className="py-1.5 pr-1">
                            <input
                              type="checkbox"
                              checked={row.include}
                              onChange={() => updateRow(row.id, { include: !row.include })}
                              className="size-4 accent-[var(--sapling-orange)]"
                            />
                          </td>
                          <td className="py-1.5 pr-2">
                            <select
                              value={row.block_id}
                              onChange={(e) => handleBlockSelect(row.id, e.target.value)}
                              className={`w-32 rounded border px-1.5 py-1 text-xs ${row.auto_matched ? "border-green-300 bg-green-50" : row.block_id ? "" : "border-amber-300 bg-amber-50"}`}
                            >
                              <option value="">{row.block_name || "Select block..."}</option>
                              {blocks.map((b) => (
                                <option key={b.id} value={b.id}>{b.name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="py-1.5 pr-2">
                            <Input
                              value={row.crop}
                              onChange={(e) => updateRow(row.id, { crop: e.target.value })}
                              className="h-7 w-24 text-xs"
                            />
                          </td>
                          <td className="py-1.5 pr-2">
                            <Input
                              value={row.cultivar}
                              onChange={(e) => updateRow(row.id, { cultivar: e.target.value })}
                              className="h-7 w-24 text-xs"
                            />
                          </td>
                          {VALUE_KEYS.map((k) => (
                            <td key={k} className="py-1.5 pr-1">
                              <Input
                                type="number"
                                step="any"
                                value={row.values[k] || ""}
                                onChange={(e) => updateValue(row.id, k, e.target.value)}
                                className={`h-7 w-16 text-right text-xs tabular-nums ${row.outlier_keys.includes(k) ? "border-red-400 bg-red-50" : ""}`}
                              />
                            </td>
                          ))}
                          <td className="py-1.5">
                            <button
                              onClick={() => setRows((prev) => prev.filter((r) => r.id !== row.id))}
                              className="text-red-400 hover:text-red-600"
                            >
                              <Trash2 className="size-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Block match summary */}
            {mode === "upload" && (
              <div className="flex flex-wrap gap-2">
                {rows.filter((r) => r.auto_matched && r.include).length > 0 && (
                  <span className="flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                    <Check className="size-3" /> {rows.filter((r) => r.auto_matched && r.include).length} auto-matched
                  </span>
                )}
                {rows.filter((r) => !r.block_id && r.include).length > 0 && (
                  <span className="flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
                    <AlertTriangle className="size-3" /> {rows.filter((r) => !r.block_id && r.include).length} unmatched — assign blocks above
                  </span>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setMode("choose");
                  setRows([]);
                }}
              >
                <ChevronLeft className="size-4" /> Start Over
              </Button>
              <Button
                onClick={handleSaveAll}
                disabled={saving || rows.filter((r) => r.include).length === 0}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                Save {rows.filter((r) => r.include).length} Analyses
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
