"use client";

/**
 * Bulk-import flow for a client. Drop a CSV/spreadsheet and the page
 * parses, validates, previews, and lets the agronomist commit in one
 * shot. Three tabs:
 *
 *   - Fields   → POST /api/clients/farms/{farm_id}/fields/bulk
 *   - Yields   → POST /api/clients/farms/{farm_id}/yields/bulk
 *   - Analyses → reuses the existing /api/soil/batch endpoint per row
 *                (one call per analysis; backend handles classification)
 *
 * Hard-line: no historical PROGRAMME import — artifacts are engine-
 * generated and not reconstructable from external sources. The
 * agronomist re-runs the wizard against imported soil + leaf data
 * to regenerate programmes.
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  ArrowLeft, AlertCircle, CheckCircle2, FileSpreadsheet, Upload,
} from "lucide-react";
import {
  parseCsvFile,
  mapFieldRow,
  mapYieldRow,
  mapSoilAnalysisRow,
  type BulkFieldRowParsed,
  type BulkYieldRowParsed,
  type BulkSoilAnalysisRowParsed,
  type ParsedSheet,
} from "@/lib/import-csv";

type TabKey = "fields" | "yields" | "analyses";

interface Farm { id: string; name: string }

export default function ImportPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [client, setClient] = useState<{ name: string } | null>(null);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmId, setFarmId] = useState<string>("");
  const [tab, setTab] = useState<TabKey>("fields");

  useEffect(() => {
    (async () => {
      try {
        const [allClients, farmsData] = await Promise.all([
          api.getAll<{ id: string; name: string }>("/api/clients"),
          api.get<Farm[]>(`/api/clients/${clientId}/farms`),
        ]);
        const c = allClients.find((cl) => cl.id === clientId);
        if (c) setClient({ name: c.name });
        setFarms(farmsData);
        if (farmsData.length === 1) setFarmId(farmsData[0].id);
      } catch {
        toast.error("Failed to load client + farms");
      }
    })();
  }, [clientId]);

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-6">
        <button
          onClick={() => router.push(`/clients/${clientId}`)}
          className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground hover:text-[var(--sapling-dark)]"
        >
          <ArrowLeft className="size-4" /> Back to client
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
            Bulk import — {client?.name ?? "…"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Drop a CSV or Excel-saved-as-CSV. Headers don&apos;t need to match exactly —
            the importer recognises common aliases (Block / Block Name / Field, Area / Size / Hectares, etc.).
          </p>
        </div>

        <Card className="mb-4">
          <CardContent className="py-4">
            <Label htmlFor="farm-select" className="text-xs text-muted-foreground">
              Target farm
            </Label>
            <select
              id="farm-select"
              value={farmId}
              onChange={(e) => setFarmId(e.target.value)}
              className="mt-1 w-full max-w-md rounded-md border bg-white px-3 py-2 text-sm"
            >
              <option value="">Select a farm…</option>
              {farms.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
            {farms.length === 0 && (
              <p className="mt-2 text-xs text-amber-700">
                This client has no farms yet. Add one on the client page first.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Tab strip */}
        <div className="mb-4 flex gap-1 rounded-lg bg-muted p-1">
          {(["fields", "yields", "analyses"] as const).map((k) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                tab === k
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-[var(--sapling-dark)]"
              }`}
            >
              {k === "fields" && "Fields / Blocks"}
              {k === "yields" && "Yield records"}
              {k === "analyses" && "Soil + leaf analyses"}
            </button>
          ))}
        </div>

        {tab === "fields" && <FieldsImport farmId={farmId} clientId={clientId} />}
        {tab === "yields" && <YieldsImport farmId={farmId} />}
        {tab === "analyses" && <AnalysesImport farmId={farmId} clientId={clientId} />}
      </div>
    </AppShell>
  );
}

// ─── Fields tab ─────────────────────────────────────────────────────

function FieldsImport({ farmId, clientId }: { farmId: string; clientId: string }) {
  const router = useRouter();
  const [sheet, setSheet] = useState<ParsedSheet | null>(null);
  const [parsed, setParsed] = useState<BulkFieldRowParsed[]>([]);
  const [conflict, setConflict] = useState<"skip" | "update">("skip");
  const [committing, setCommitting] = useState(false);

  const handleFile = async (file: File) => {
    try {
      const s = await parseCsvFile(file);
      setSheet(s);
      setParsed(s.rows.map((r, i) => mapFieldRow(r, i)));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to parse CSV");
    }
  };

  const validRows = parsed.filter((r) => r.errors.length === 0 && r.name);
  const errorRows = parsed.filter((r) => r.errors.length > 0);

  const commit = async () => {
    if (!farmId) {
      toast.error("Pick a farm first");
      return;
    }
    if (validRows.length === 0) {
      toast.error("No valid rows to import");
      return;
    }
    setCommitting(true);
    try {
      const res = await api.post<{ created: number; updated: number; skipped: number }>(
        `/api/clients/farms/${farmId}/fields/bulk`,
        { farm_id: farmId, rows: validRows.map((r) => ({ ...r, warnings: undefined, errors: undefined })), on_conflict: conflict },
      );
      toast.success(
        `${res.created} created · ${res.updated} updated · ${res.skipped} skipped`,
      );
      router.push(`/clients/${clientId}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <FilePicker accept=".csv,text/csv" onFile={handleFile} hint="CSV exported from your fields spreadsheet" />

      {sheet && (
        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm">
                {parsed.length} row{parsed.length !== 1 ? "s" : ""} parsed ·
                {" "}<span className="text-emerald-700">{validRows.length} ok</span> ·
                {" "}<span className="text-red-700">{errorRows.length} with errors</span>
              </p>
              <div className="flex items-center gap-2 text-xs">
                <Label className="text-xs text-muted-foreground">If field exists:</Label>
                <select
                  value={conflict}
                  onChange={(e) => setConflict(e.target.value as "skip" | "update")}
                  className="rounded border bg-white px-2 py-1 text-xs"
                >
                  <option value="skip">Skip (keep existing)</option>
                  <option value="update">Update (overwrite blanks + new values)</option>
                </select>
              </div>
            </div>

            <PreviewTable
              rows={parsed.slice(0, 50)}
              columns={[
                ["Name", (r) => r.name],
                ["Crop", (r) => `${r.crop ?? "—"}${r.cultivar ? ` · ${r.cultivar}` : ""}`],
                ["Area (ha)", (r) => fmt(r.size_ha)],
                ["Tree age", (r) => fmt(r.tree_age)],
                ["Pop/ha", (r) => fmt(r.pop_per_ha)],
                ["Irrigation", (r) => r.irrigation_type ?? "—"],
                ["Fert?", (r) => (r.fertigation_capable === true ? "yes" : r.fertigation_capable === false ? "no" : "—")],
                ["Issues", (r) => issuesCell(r.errors, r.warnings)],
              ]}
            />
            {parsed.length > 50 && (
              <p className="mt-2 text-xs text-muted-foreground">
                Showing first 50 rows · {parsed.length - 50} more will be imported
              </p>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setSheet(null); setParsed([]); }}>
                Discard
              </Button>
              <Button
                onClick={commit}
                disabled={committing || validRows.length === 0 || !farmId}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {committing ? "Importing…" : `Import ${validRows.length} field${validRows.length !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Yields tab ─────────────────────────────────────────────────────

function YieldsImport({ farmId }: { farmId: string }) {
  const [sheet, setSheet] = useState<ParsedSheet | null>(null);
  const [parsed, setParsed] = useState<BulkYieldRowParsed[]>([]);
  const [conflict, setConflict] = useState<"skip" | "update">("skip");
  const [committing, setCommitting] = useState(false);

  const handleFile = async (file: File) => {
    try {
      const s = await parseCsvFile(file);
      setSheet(s);
      setParsed(s.rows.map((r) => mapYieldRow(r)));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to parse CSV");
    }
  };

  const validRows = parsed.filter((r) => r.errors.length === 0);
  const errorRows = parsed.filter((r) => r.errors.length > 0);

  const commit = async () => {
    if (!farmId) {
      toast.error("Pick a farm first");
      return;
    }
    if (validRows.length === 0) {
      toast.error("No valid rows to import");
      return;
    }
    setCommitting(true);
    try {
      const res = await api.post<{
        created: number; updated: number; skipped: number; unmatched: string[];
      }>(`/api/clients/farms/${farmId}/yields/bulk`, {
        farm_id: farmId,
        rows: validRows.map((r) => ({
          field_name: r.field_name,
          season: r.season,
          yield_actual: r.yield_actual,
          yield_unit: r.yield_unit,
          harvest_date: r.harvest_date,
          source: r.source,
          notes: r.notes,
        })),
        on_conflict: conflict,
      });
      const unmatchedMsg = res.unmatched.length > 0
        ? ` · ${res.unmatched.length} unmatched (no field with that name)`
        : "";
      toast.success(
        `${res.created} created · ${res.updated} updated · ${res.skipped} skipped${unmatchedMsg}`,
      );
      setSheet(null); setParsed([]);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <FilePicker accept=".csv,text/csv" onFile={handleFile} hint="CSV with columns: Block / Season / Yield / Yield Unit (optional Harvest Date)" />

      {sheet && (
        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm">
                {parsed.length} row{parsed.length !== 1 ? "s" : ""} parsed ·
                {" "}<span className="text-emerald-700">{validRows.length} ok</span> ·
                {" "}<span className="text-red-700">{errorRows.length} with errors</span>
              </p>
              <div className="flex items-center gap-2 text-xs">
                <Label className="text-xs text-muted-foreground">If yield exists:</Label>
                <select
                  value={conflict}
                  onChange={(e) => setConflict(e.target.value as "skip" | "update")}
                  className="rounded border bg-white px-2 py-1 text-xs"
                >
                  <option value="skip">Skip</option>
                  <option value="update">Overwrite</option>
                </select>
              </div>
            </div>

            <PreviewTable
              rows={parsed.slice(0, 50)}
              columns={[
                ["Block", (r) => r.field_name],
                ["Season", (r) => r.season],
                ["Yield", (r) => fmt(r.yield_actual)],
                ["Unit", (r) => r.yield_unit],
                ["Harvest", (r) => r.harvest_date ?? "—"],
                ["Issues", (r) => issuesCell(r.errors, r.warnings)],
              ]}
            />
            {parsed.length > 50 && (
              <p className="mt-2 text-xs text-muted-foreground">
                Showing first 50 rows · {parsed.length - 50} more will be imported
              </p>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setSheet(null); setParsed([]); }}>
                Discard
              </Button>
              <Button
                onClick={commit}
                disabled={committing || validRows.length === 0 || !farmId}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {committing ? "Importing…" : `Import ${validRows.length} yield record${validRows.length !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Analyses tab — soil-analysis CSV bulk import ───────────────────

interface FieldLookup { id: string; name: string }

function AnalysesImport({ farmId, clientId }: { farmId: string; clientId: string }) {
  const [sheet, setSheet] = useState<ParsedSheet | null>(null);
  const [parsed, setParsed] = useState<BulkSoilAnalysisRowParsed[]>([]);
  const [fields, setFields] = useState<FieldLookup[]>([]);
  const [labName, setLabName] = useState("");
  const [analysisDate, setAnalysisDate] = useState("");
  const [conflict, setConflict] = useState<"replace" | "keep_both_new_latest">("replace");
  const [committing, setCommitting] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [client, setClient] = useState<{ name: string } | null>(null);
  useEffect(() => {
    api.getAll<{ id: string; name: string }>("/api/clients")
      .then((cs) => setClient(cs.find((c) => c.id === clientId) ?? null))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!farmId) {
      setFields([]);
      return;
    }
    api.get<FieldLookup[]>(`/api/clients/farms/${farmId}/fields`)
      .then(setFields)
      .catch(() => setFields([]));
  }, [farmId]);

  const handleFile = async (file: File) => {
    try {
      const s = await parseCsvFile(file);
      setSheet(s);
      setParsed(s.rows.map((r) => mapSoilAnalysisRow(r, {
        lab_name: labName || undefined,
        analysis_date: analysisDate || undefined,
      })));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to parse CSV");
    }
  };

  // Resolve field name → field_id from the farm's fields list
  const resolveField = (name: string): string | null => {
    const norm = name.trim().toLowerCase();
    return fields.find((f) => f.name.trim().toLowerCase() === norm)?.id ?? null;
  };

  const enriched = parsed.map((r) => {
    const field_id = resolveField(r.field_name);
    return {
      ...r,
      field_id,
      unmatched: !field_id,
    };
  });

  const validRows = enriched.filter((r) => r.errors.length === 0 && r.field_id);
  const errorRows = enriched.filter((r) => r.errors.length > 0);
  const unmatched = enriched.filter((r) => r.errors.length === 0 && !r.field_id);
  const clientName = client?.name ?? "";

  const commit = async () => {
    if (!farmId) {
      toast.error("Pick a farm first");
      return;
    }
    if (validRows.length === 0) {
      toast.error("No valid rows to import");
      return;
    }
    setCommitting(true);
    setProgress({ done: 0, total: validRows.length });

    // Batch endpoint accepts up to one analysis per row, but we hit it
    // per-row to keep classification stable + give clear error feedback.
    let okCount = 0;
    const errors: string[] = [];
    for (let i = 0; i < validRows.length; i++) {
      const row = validRows[i];
      try {
        await api.post(`/api/soil/batch`, {
          client_id: clientId,
          farm_id: farmId,
          lab_name: row.lab_name || labName || undefined,
          analysis_date: row.analysis_date || analysisDate || undefined,
          conflict_resolution: conflict,
          items: [{
            field_id: row.field_id,
            field_name: row.field_name,
            crop: row.crop,
            cultivar: row.cultivar,
            yield_target: row.yield_target,
            yield_unit: row.yield_unit,
            analysis_type: "soil",
            soil_values: row.soil_values,
          }],
        });
        okCount++;
      } catch (e) {
        errors.push(`${row.field_name}: ${e instanceof Error ? e.message : "failed"}`);
      }
      setProgress({ done: i + 1, total: validRows.length });
    }

    if (errors.length === 0) {
      toast.success(`Imported ${okCount} soil analyses`);
    } else {
      toast.warning(
        `${okCount} ok · ${errors.length} failed`,
        { description: errors.slice(0, 3).join(" / ") },
      );
    }
    setCommitting(false);
    setSheet(null);
    setParsed([]);
  };

  void clientName; // intentionally referenced for future toast detail

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="py-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="space-y-1">
              <Label className="text-xs">Lab name (default)</Label>
              <input
                value={labName}
                onChange={(e) => setLabName(e.target.value)}
                placeholder="e.g. NViroTek"
                className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Analysis date (default)</Label>
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">If field has a recent analysis</Label>
              <select
                value={conflict}
                onChange={(e) => setConflict(e.target.value as "replace" | "keep_both_new_latest")}
                className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              >
                <option value="replace">Replace</option>
                <option value="keep_both_new_latest">Keep both (new becomes latest)</option>
              </select>
            </div>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            Per-row Lab / Date columns in the CSV override the defaults above.
          </p>
        </CardContent>
      </Card>

      <FilePicker
        accept=".csv,text/csv"
        onFile={handleFile}
        hint="CSV with one row per block-analysis. Headers like Block, Date, pH, P, K, Ca, Mg, Zn, B, etc. are auto-recognised."
      />

      {sheet && (
        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm">
                {parsed.length} row{parsed.length !== 1 ? "s" : ""} parsed ·
                {" "}<span className="text-emerald-700">{validRows.length} ok</span> ·
                {unmatched.length > 0 && (
                  <> <span className="text-amber-700">{unmatched.length} unmatched</span> · </>
                )}
                {" "}<span className="text-red-700">{errorRows.length} with errors</span>
              </p>
            </div>

            {unmatched.length > 0 && (
              <div className="mb-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
                <p className="font-medium">Unmatched block names — won&apos;t be imported:</p>
                <ul className="mt-1 list-disc pl-5">
                  {unmatched.slice(0, 5).map((r, i) => (
                    <li key={i}>{r.field_name}</li>
                  ))}
                  {unmatched.length > 5 && <li>… {unmatched.length - 5} more</li>}
                </ul>
                <p className="mt-1">
                  Bulk-import the fields first (or rename the blocks in the CSV) and re-upload.
                </p>
              </div>
            )}

            <PreviewTable
              rows={enriched.slice(0, 50)}
              columns={[
                ["Block", (r) => `${r.field_name}${r.field_id ? "" : " ⚠"}`],
                ["Date", (r) => r.analysis_date ?? analysisDate ?? "—"],
                ["Crop", (r) => r.crop ?? "—"],
                ["Lab", (r) => r.lab_name ?? labName ?? "—"],
                ["Params", (r) => `${Object.keys(r.soil_values).length}`],
                ["Issues", (r) => issuesCell(r.errors, r.warnings)],
              ]}
            />
            {parsed.length > 50 && (
              <p className="mt-2 text-xs text-muted-foreground">
                Showing first 50 rows · {parsed.length - 50} more will be processed
              </p>
            )}

            {committing && (
              <div className="mt-3 rounded-md border bg-muted/30 px-3 py-2 text-xs">
                Importing… {progress.done} / {progress.total}
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full bg-[var(--sapling-orange)] transition-all"
                    style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }}
                  />
                </div>
              </div>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setSheet(null); setParsed([]); }} disabled={committing}>
                Discard
              </Button>
              <Button
                onClick={commit}
                disabled={committing || validRows.length === 0 || !farmId}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {committing
                  ? "Importing…"
                  : `Import ${validRows.length} ${validRows.length === 1 ? "analysis" : "analyses"}`}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Shared bits ────────────────────────────────────────────────────

function FilePicker({
  accept, onFile, hint,
}: { accept: string; onFile: (f: File) => void; hint: string }) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center gap-3 py-8 text-center">
        <FileSpreadsheet className="size-8 text-muted-foreground" />
        <div>
          <Label className="cursor-pointer text-sm font-medium text-[var(--sapling-orange)] hover:underline">
            <Upload className="mr-1 inline size-4" />
            Choose file
            <input
              type="file"
              accept={accept}
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onFile(f);
              }}
            />
          </Label>
          <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
        </div>
      </CardContent>
    </Card>
  );
}

interface PreviewTableProps<T> {
  rows: T[];
  columns: Array<[label: string, render: (r: T) => React.ReactNode]>;
}

function PreviewTable<T>({ rows, columns }: PreviewTableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b bg-muted/30 text-left">
            {columns.map(([label]) => (
              <th key={label} className="px-2 py-1.5 font-medium">{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-muted/20">
              {columns.map(([label, render]) => (
                <td key={label} className="px-2 py-1.5">{render(r)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function issuesCell(errors: string[], warnings: string[]) {
  if (errors.length === 0 && warnings.length === 0) {
    return <CheckCircle2 className="size-3.5 text-emerald-600" />;
  }
  return (
    <div className="flex items-center gap-1">
      {errors.length > 0 && (
        <span title={errors.join(" · ")} className="flex items-center gap-0.5 text-red-700">
          <AlertCircle className="size-3.5" />
          {errors.length}
        </span>
      )}
      {warnings.length > 0 && (
        <span title={warnings.join(" · ")} className="flex items-center gap-0.5 text-amber-700">
          <AlertCircle className="size-3.5" />
          {warnings.length}
        </span>
      )}
    </div>
  );
}

function fmt(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
