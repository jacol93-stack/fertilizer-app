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

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  ArrowLeft, AlertCircle, CheckCircle2, FileSpreadsheet, Upload, Download, Loader2, X,
} from "lucide-react";
import {
  parseSpreadsheetFile,
  mapFieldRow,
  mapYieldRow,
  type BulkFieldRowParsed,
  type BulkYieldRowParsed,
  type BulkSoilAnalysisRowParsed,
  type ParsedSheet,
} from "@/lib/import-csv";
import { API_URL } from "@/lib/api";
import { createClient } from "@/lib/supabase";

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
    <>
      <div>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
            Bulk import — {client?.name ?? "…"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Pick the right tab below. Fields and Yields use a downloadable template;
            Analyses takes the lab&apos;s report directly (PDF / photo / xlsx) — soil
            or leaf, AI extracts every sample. The yields template pre-populates
            with this farm&apos;s existing blocks once a farm is selected.
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
    </>
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
      const s = await parseSpreadsheetFile(file);
      setSheet(s);
      setParsed(s.rows.map((r, i) => mapFieldRow(r, i)));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to parse file");
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
      <TemplateDownloadButton
        label="Download fields template (.xlsx)"
        hint="Open in Excel, fill in the rows, then save as CSV before uploading."
        path="/api/clients/templates/fields"
        filename="sapling-fields-template.xlsx"
      />

      <FilePicker
        accept=".xlsx,.xls,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onFile={handleFile}
        hint="Upload the filled-in template — .xlsx works directly, or save as CSV first."
      />

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
      const s = await parseSpreadsheetFile(file);
      setSheet(s);
      setParsed(s.rows.map((r) => mapYieldRow(r)));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to parse file");
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
      <TemplateDownloadButton
        label="Download yields template (.xlsx)"
        hint={
          farmId
            ? "Pre-populated with this farm's existing blocks. Open in Excel, fill in season + yield per row, save as CSV, then upload."
            : "Pick a farm above first — the template pre-populates with that farm's blocks."
        }
        path={farmId ? `/api/clients/farms/${farmId}/templates/yields` : null}
        filename="sapling-yields-template.xlsx"
      />

      <FilePicker
        accept=".xlsx,.xls,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onFile={handleFile}
        hint="Upload the filled-in template — .xlsx works directly, or save as CSV first."
      />

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

type AnalysisMode = "soil" | "leaf";

function AnalysesImport({ farmId, clientId }: { farmId: string; clientId: string }) {
  const [sheet, setSheet] = useState<ParsedSheet | null>(null);
  const [parsed, setParsed] = useState<BulkSoilAnalysisRowParsed[]>([]);
  const [fields, setFields] = useState<FieldLookup[]>([]);
  const [labName, setLabName] = useState("");
  const [analysisDate, setAnalysisDate] = useState("");
  // Soil vs leaf — controls extract endpoint, commit analysis_type,
  // duplicate-check table. User can override the auto-detected default
  // before triggering extract.
  const [mode, setMode] = useState<AnalysisMode>("soil");
  // Soil/leaf analyses are point-in-time records. Always append a new
  // row; never overwrite history. Duplicates (same field + same date)
  // are detected pre-flight and pre-skipped. The duplicate cache
  // mirrors whichever table corresponds to the selected mode — soil
  // and leaf live in separate tables, so no cross-contamination.
  const existingAnalysesRef = useRef<Array<{
    field_id: string | null;
    analysis_date: string | null;
  }>>([]);
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
      existingAnalysesRef.current = [];
      return;
    }
    api.get<FieldLookup[]>(`/api/clients/farms/${farmId}/fields`)
      .then(setFields)
      .catch(() => setFields([]));
    // Pre-fetch the farm's existing analyses in the active mode so we
    // can flag duplicates at preview time. The leaf table uses
    // `sample_date` (not `analysis_date`); we normalise the field name
    // for the in-memory cache so the duplicate check stays mode-agnostic.
    const path = mode === "soil"
      ? `/api/soil/?farm_id=${farmId}&limit=500`
      : `/api/leaf/?farm_id=${farmId}&limit=500`;
    type ListedAnalysis = {
      field_id: string | null;
      analysis_date?: string | null;
      sample_date?: string | null;
    };
    api.get<{ items: ListedAnalysis[] }>(path)
      .then((res) => {
        existingAnalysesRef.current = (res.items ?? []).map((a) => ({
          field_id: a.field_id,
          analysis_date: a.analysis_date ?? a.sample_date ?? null,
        }));
      })
      .catch(() => { existingAnalysesRef.current = []; });
  }, [farmId, mode]);

  const [extracting, setExtracting] = useState(false);
  // Staged file — selected but not yet processed. The agronomist gets
  // a chance to review the auto-detected mode + adjust lab name + date
  // before paying the API call. Avoids the previous footgun where
  // extraction fired the moment a file was picked, leaving zero room
  // to override the report-type toggle.
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const handlePickFile = (file: File) => {
    setPendingFile(file);
    // Filename heuristic flips the toggle straight away so the user
    // sees the detected report type alongside the file name and can
    // override before clicking Start.
    const detectedMode = detectModeFromFilename(file.name);
    if (detectedMode && detectedMode !== mode) {
      setMode(detectedMode);
    }
  };

  const handleStartExtraction = async () => {
    if (!pendingFile) return;
    const file = pendingFile;
    // Lab analyses don't have a fixed column shape — every lab uses
    // different parameter names + orderings + units, and reports
    // commonly bundle 10-30 blocks in one file. We dispatch every
    // analyses upload (PDF / image / xlsx / csv) through the AI lab
    // extractor so the agronomist never has to think about which
    // template format the lab used.
    const effectiveMode = mode;

    setExtracting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (labName) formData.append("lab_name_hint", labName);
      if (clientId) formData.append("client_id", clientId);

      const token = (
        await createClient().auth.getSession()
      ).data.session?.access_token;
      const extractPath = effectiveMode === "leaf"
        ? "/api/leaf/extract"
        : "/api/soil/extract";
      const res = await fetch(`${API_URL}${extractPath}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = (body as { detail?: string }).detail;
        throw new Error(detail || `Extract failed (HTTP ${res.status})`);
      }
      const data = await res.json();
      const samples: Array<{
        block_name?: string | null;
        sample_id?: string | null;
        crop?: string | null;
        cultivar?: string | null;
        values?: Record<string, unknown>;
      }> = data.samples ?? [];

      const detectedLab = (data.lab_name || labName) as string | undefined;
      const detectedDate = (data.analysis_date || analysisDate) as string | undefined;
      if (data.lab_name && !labName) setLabName(data.lab_name);
      if (data.analysis_date && !analysisDate) setAnalysisDate(data.analysis_date);

      // AI department mismatch — the AI reads the document header and
      // tells us "Leaf" or "Soil". If that disagrees with the toggle
      // (e.g. user uploaded a leaf file with the Soil toggle set),
      // surface a clear warning. The values are already keyed in
      // whichever schema we requested, so the safer move is to alert
      // the user + offer the correct re-run rather than silently
      // committing wrong-shaped values.
      const aiDept = String((data as { department?: string }).department || "").toLowerCase();
      const aiSaysLeaf = aiDept.includes("leaf");
      const aiSaysSoil = aiDept.includes("soil");
      if (aiSaysLeaf && effectiveMode !== "leaf") {
        toast.warning(
          "AI thinks this is a leaf report but you have Soil selected. Switch the toggle to Leaf and re-upload to get correct schema.",
          { duration: 12000 },
        );
      } else if (aiSaysSoil && effectiveMode !== "soil") {
        toast.warning(
          "AI thinks this is a soil report but you have Leaf selected. Switch the toggle to Soil and re-upload to get correct schema.",
          { duration: 12000 },
        );
      }

      // Reality of dealing with farmers — many lab files have no date
      // anywhere in the document, but the filename usually carries the
      // year ("MFB Trust Grond 2022.xls"). Fall back to mid-year for
      // that year so the engine has *something* dated; agronomist can
      // adjust before commit.
      if (!data.analysis_date && !analysisDate) {
        const yearMatch = file.name.match(/\b(20[2-3]\d)\b/);
        if (yearMatch) {
          setAnalysisDate(`${yearMatch[1]}-06-15`);
          toast.info(
            `No date in the file — guessed ${yearMatch[1]}-06-15 from the filename. Adjust above if you have the actual sample date.`,
          );
        }
      }

      // Filter out norm / reference / standard rows that some labs
      // include in their tables.
      const realSamples = samples.filter((s) => {
        const name = (s.block_name || s.sample_id || "").toLowerCase();
        return !name.includes("norm") && !name.includes("reference") && !name.includes("standard");
      });

      // Convert the AI samples into the existing preview-row shape so
      // the unmatched-block warning + commit pipeline below works
      // unchanged. Numeric coercion mirrors what the deterministic
      // path used to do — silently drop non-numeric / blank values.
      const parsedRows: BulkSoilAnalysisRowParsed[] = realSamples.map((s) => {
        const fieldName = (s.block_name || s.sample_id || "").trim();
        const soilValues: Record<string, number | null> = {};
        for (const [k, v] of Object.entries(s.values ?? {})) {
          if (v == null || v === "") continue;
          const n = typeof v === "number" ? v : parseFloat(String(v).replace(/,/g, "."));
          if (Number.isFinite(n)) soilValues[k] = n;
        }
        const errors: string[] = [];
        if (!fieldName) errors.push("Block name not detected — assign manually before commit");
        if (Object.keys(soilValues).length === 0) {
          errors.push("No numeric values extracted from this row");
        }
        return {
          field_name: fieldName,
          crop: s.crop ?? null,
          cultivar: s.cultivar ?? null,
          lab_name: detectedLab || null,
          // Normalise empty strings to null so the form-level fallback
          // in effectiveDateFor takes over via short-circuit ||.
          analysis_date: detectedDate || null,
          yield_target: null,
          yield_unit: null,
          soil_values: soilValues,
          warnings: [],
          errors,
        };
      });

      setSheet({
        headers: Object.keys(realSamples[0]?.values ?? {}),
        rows: [],
        raw_row_count: parsedRows.length,
      });
      setParsed(parsedRows);
      // New extraction = clean slate for any prior manual overrides.
      setManualField({});

      // Pre-flight duplicate detection: pre-tick Skip on any row whose
      // resolved (field_id, analysis_date) already exists for this farm.
      // The agronomist can untick if they actually want a second
      // record for the same date (rare, e.g. correcting a typo in the
      // first upload).
      const dupSkip: Record<number, boolean> = {};
      // `||` (not `??`) so an empty per-row string falls through to the
      // detected/form date instead of evaluating as a real value.
      const effectiveDate = (r: BulkSoilAnalysisRowParsed) =>
        r.analysis_date || detectedDate || null;
      parsedRows.forEach((r, i) => {
        const targetField = canonicaliseBlockName(r.field_name);
        if (!targetField) return;
        const fieldId =
          fields.find((f) => canonicaliseBlockName(f.name) === targetField)?.id;
        if (!fieldId) return;
        const date = effectiveDate(r);
        if (!date) return;
        const isDup = existingAnalysesRef.current.some(
          (a) => a.field_id === fieldId && a.analysis_date === date,
        );
        if (isDup) dupSkip[i] = true;
      });
      setSkipped(dupSkip);

      const conf = data.confidence ? ` · AI confidence: ${data.confidence}` : "";
      const dupCount = Object.keys(dupSkip).length;
      const dupMsg = dupCount > 0
        ? ` · ${dupCount} likely duplicate${dupCount === 1 ? "" : "s"} pre-skipped`
        : "";
      toast.success(
        `Extracted ${parsedRows.length} ${parsedRows.length === 1 ? "sample" : "samples"}${conf}${dupMsg}`,
      );
      // File processed cleanly — clear the staged file so the picker
      // returns to its idle state. Failures keep the file staged so
      // the user can retry without re-selecting.
      setPendingFile(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to extract lab report");
    } finally {
      setExtracting(false);
    }
  };

  // Resolve field name → field_id from the farm's fields list. SA labs
  // and farms write block names in mixed Afrikaans/English ("Blok 1"
  // vs "Block 1"), with stray accents and leading zeros. We canonicalise
  // both sides before comparing so the auto-match works regardless of
  // which language the field/lab are using.
  const resolveField = (name: string): string | null => {
    const target = canonicaliseBlockName(name);
    if (!target) return null;
    return (
      fields.find((f) => canonicaliseBlockName(f.name) === target)?.id ?? null
    );
  };

  // Per-row manual overrides. Indexed by row position in `parsed`.
  // `manualField[i]` overrides the auto-matcher (use to map a "Block
  // 15/17" combined row onto whichever single block the user wants).
  // `skipped[i]` excludes the row from commit (use for combined rows
  // the user can't safely split, junk lines, etc.).
  const [manualField, setManualField] = useState<Record<number, string>>({});
  const [skipped, setSkipped] = useState<Record<number, boolean>>({});

  // `||` (not `??`) so an empty per-row string falls through to the
  // form-level analysisDate. This matters when the AI returned no date
  // and the user typed one in the form *after* extraction completed —
  // the empty per-row value would otherwise win against the new form date.
  const effectiveDateFor = (r: BulkSoilAnalysisRowParsed) =>
    r.analysis_date || analysisDate || null;

  const enriched = parsed.map((r, i) => {
    const auto = resolveField(r.field_name);
    const override = manualField[i];
    const field_id = override ?? auto;
    const date = effectiveDateFor(r);
    const is_duplicate =
      !!field_id && !!date &&
      existingAnalysesRef.current.some(
        (a) => a.field_id === field_id && a.analysis_date === date,
      );
    return {
      ...r,
      field_id,
      auto_matched: !!auto,
      unmatched: !field_id,
      skipped: !!skipped[i],
      is_duplicate,
      missing_date: !date,
      idx: i,
    };
  });

  // Every persisted analysis must have a real sample date — historical
  // view sorts on it, duplicate detection keys on it. Rows with no
  // resolved date (no AI date + no per-row date + no form-default date)
  // are blocked from commit until the agronomist supplies one.
  const validRows = enriched.filter(
    (r) => !r.skipped && r.errors.length === 0 && r.field_id && !r.missing_date,
  );
  const errorRows = enriched.filter((r) => !r.skipped && r.errors.length > 0);
  const unmatched = enriched.filter(
    (r) => !r.skipped && r.errors.length === 0 && !r.field_id,
  );
  const skippedRows = enriched.filter((r) => r.skipped);
  const clientName = client?.name ?? "";

  const commit = async () => {
    if (!farmId) {
      toast.error("Pick a farm first");
      return;
    }
    const undated = enriched.filter((r) => !r.skipped && r.missing_date);
    if (undated.length > 0) {
      toast.error(
        `Set an Analysis date before importing — ${undated.length} row${undated.length === 1 ? " has" : "s have"} no date.`,
      );
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
          analysis_date: row.analysis_date || analysisDate,
          // Soil analyses are append-only in bulk import. Each upload
          // creates a new historical record; the field's latest_analysis_id
          // moves to the new one. Pre-flight duplicate detection prevents
          // re-uploading the same (field, date) twice.
          conflict_resolution: "keep_both_new_latest",
          items: [{
            field_id: row.field_id,
            field_name: row.field_name,
            crop: row.crop,
            cultivar: row.cultivar,
            yield_target: row.yield_target,
            yield_unit: row.yield_unit,
            // Mode toggle controls whether this row lands in
            // soil_analyses or leaf_analyses. /api/soil/batch routes by
            // this discriminator (see soil.py line 992).
            analysis_type: mode,
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
          <div className="mb-3">
            <Label className="text-xs">Report type</Label>
            <div className="mt-1 flex gap-1 rounded-md bg-muted p-0.5">
              {(["soil", "leaf"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`flex-1 rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                    mode === m
                      ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                      : "text-muted-foreground hover:text-[var(--sapling-dark)]"
                  }`}
                >
                  {m === "soil" ? "Soil" : "Leaf"}
                </button>
              ))}
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              Auto-detected from the filename when you pick a file.
              {mode === "soil"
                ? " Soil reports land in the soil-analyses table."
                : " Leaf reports land in the leaf-analyses table — separate from soil, with separate duplicate detection."}
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
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
              <Label className="text-xs">
                Analysis date <span className="text-red-600">*</span>
              </Label>
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                className={`w-full rounded-md border bg-white px-3 py-2 text-sm ${
                  parsed.length > 0 && !analysisDate ? "border-red-500" : ""
                }`}
                required
              />
            </div>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            AI auto-detects lab name + analysis date from the report — these
            defaults only fill in when the document doesn&apos;t carry them.
            A date is required on every row before commit.
            Imports always append a new historical record; existing analyses
            are never overwritten.
          </p>
        </CardContent>
      </Card>

      {pendingFile && !extracting ? (
        <Card className="border-[var(--sapling-orange)]/40 bg-orange-50/30">
          <CardContent className="flex flex-col gap-3 py-5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <FileSpreadsheet className="mt-0.5 size-5 text-[var(--sapling-orange)]" />
                <div>
                  <p className="text-sm font-medium text-[var(--sapling-dark)]">
                    {pendingFile.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(pendingFile.size / 1024).toFixed(0)} KB · ready to process as a{" "}
                    <span className="font-medium">
                      {mode === "soil" ? "soil" : "leaf"}
                    </span>{" "}
                    report
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPendingFile(null)}
                className="shrink-0 text-muted-foreground"
              >
                <X className="size-4" />
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Confirm the report type above and adjust the lab name / date
              defaults if needed, then click Start. The AI call only runs once
              you click Start.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPendingFile(null)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleStartExtraction}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                Start extraction
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <FilePicker
          accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.xlsx,.xls,.csv,application/pdf,image/*,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
          onFile={handlePickFile}
          busy={extracting}
          busyLabel="Reading lab report with AI…"
          hint={
            extracting
              ? "Multi-page reports usually take 10-30s. Don't re-upload — the response is on its way."
              : "Upload the lab report directly — PDF, photo, or the lab's xlsx export. Pick a file, then click Start to run the AI extractor."
          }
        />
      )}

      {sheet && (
        <Card>
          <CardContent className="py-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-sm">
                {parsed.length} row{parsed.length !== 1 ? "s" : ""} parsed ·
                {" "}<span className="text-emerald-700">{validRows.length} ok</span> ·
                {unmatched.length > 0 && (
                  <> <span className="text-amber-700">{unmatched.length} unassigned</span> · </>
                )}
                {skippedRows.length > 0 && (
                  <> <span className="text-gray-500">{skippedRows.length} skipped</span> · </>
                )}
                {" "}<span className="text-red-700">{errorRows.length} with errors</span>
              </p>
            </div>

            {unmatched.length > 0 && (
              <div className="mb-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900">
                <p className="font-medium">
                  {unmatched.length} sample{unmatched.length === 1 ? "" : "s"} couldn&apos;t auto-match a field.
                </p>
                <p className="mt-0.5">
                  Pick a field in the dropdown below, or tick Skip to exclude. Combined entries like &quot;Block 15/17&quot; → assign to one block + skip the other if needed, or split manually after import.
                </p>
              </div>
            )}

            {enriched.some((r) => !r.skipped && r.missing_date) && (
              <div className="mb-3 rounded-md border border-red-300 bg-red-50 p-3 text-xs text-red-900">
                <p className="font-medium">
                  Set an Analysis date above before importing.
                </p>
                <p className="mt-0.5">
                  Neither the document nor the filename carried a date. Type the actual sample date in the &quot;Analysis date&quot; field — every persisted record needs one for the historical timeline + duplicate detection.
                </p>
              </div>
            )}

            <SamplePreviewTable
              rows={enriched.slice(0, 50)}
              fields={fields}
              labName={labName}
              analysisDate={analysisDate}
              onAssign={(idx, fieldId) =>
                setManualField((prev) => {
                  const next = { ...prev };
                  if (fieldId) next[idx] = fieldId;
                  else delete next[idx];
                  return next;
                })
              }
              onSkipToggle={(idx, value) =>
                setSkipped((prev) => ({ ...prev, [idx]: value }))
              }
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
              <Button
                variant="outline"
                onClick={() => {
                  setSheet(null);
                  setParsed([]);
                  setManualField({});
                  setSkipped({});
                  setPendingFile(null);
                }}
                disabled={committing}
              >
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

function TemplateDownloadButton({
  label, hint, path, filename,
}: {
  label: string;
  hint: string;
  path: string | null;
  filename: string;
}) {
  const [busy, setBusy] = useState(false);
  const handleClick = async () => {
    if (!path) return;
    setBusy(true);
    try {
      const blob = await api.getBlob(path);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to download template");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="border-emerald-200 bg-emerald-50/40">
      <CardContent className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-muted-foreground">{hint}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={handleClick}
          disabled={busy || !path}
          className="shrink-0"
        >
          <Download className="mr-1.5 size-4" />
          {busy ? "Preparing…" : label}
        </Button>
      </CardContent>
    </Card>
  );
}

function FilePicker({
  accept, onFile, hint, busy = false, busyLabel,
}: {
  accept: string;
  onFile: (f: File) => void;
  hint: string;
  busy?: boolean;
  busyLabel?: string;
}) {
  return (
    <Card
      className={`border-dashed transition-colors ${
        busy ? "border-[var(--sapling-orange)] bg-orange-50/40" : ""
      }`}
    >
      <CardContent className="flex flex-col items-center justify-center gap-3 py-8 text-center">
        {busy ? (
          <>
            <Loader2 className="size-8 animate-spin text-[var(--sapling-orange)]" />
            <div>
              <p className="text-sm font-medium text-[var(--sapling-dark)]">
                {busyLabel ?? "Processing…"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
            </div>
          </>
        ) : (
          <>
            <FileSpreadsheet className="size-8 text-muted-foreground" />
            <div>
              <Label className="cursor-pointer text-sm font-medium text-[var(--sapling-orange)] hover:underline">
                <Upload className="mr-1 inline size-4" />
                Choose file
                <input
                  type="file"
                  accept={accept}
                  className="hidden"
                  disabled={busy}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) onFile(f);
                    // Reset so the same file can be picked again after a failure.
                    e.target.value = "";
                  }}
                />
              </Label>
              <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
            </div>
          </>
        )}
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

interface SamplePreviewRow extends BulkSoilAnalysisRowParsed {
  field_id: string | null;
  auto_matched: boolean;
  unmatched: boolean;
  skipped: boolean;
  is_duplicate: boolean;
  idx: number;
}

function SamplePreviewTable({
  rows, fields, labName, analysisDate, onAssign, onSkipToggle,
}: {
  rows: SamplePreviewRow[];
  fields: { id: string; name: string }[];
  labName: string;
  analysisDate: string;
  onAssign: (idx: number, fieldId: string | null) => void;
  onSkipToggle: (idx: number, value: boolean) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b bg-muted/30 text-left">
            <th className="px-2 py-1.5 font-medium">Lab block</th>
            <th className="px-2 py-1.5 font-medium">Assigned to field</th>
            <th className="px-2 py-1.5 font-medium">Date</th>
            <th className="px-2 py-1.5 font-medium">Crop</th>
            <th className="px-2 py-1.5 font-medium">Lab</th>
            <th className="px-2 py-1.5 font-medium">Params</th>
            <th className="px-2 py-1.5 font-medium">Skip</th>
            <th className="px-2 py-1.5 font-medium">Issues</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const rowClass = r.skipped
              ? "bg-gray-50 text-gray-400"
              : r.is_duplicate
                ? "bg-amber-100/40"
                : r.unmatched
                  ? "bg-amber-50/50"
                  : "";
            return (
              <tr key={r.idx} className={`border-b last:border-0 hover:bg-muted/20 ${rowClass}`}>
                <td className="px-2 py-1.5">
                  {r.field_name || <span className="text-gray-400">—</span>}
                </td>
                <td className="px-2 py-1.5">
                  <select
                    value={r.field_id ?? ""}
                    onChange={(e) => onAssign(r.idx, e.target.value || null)}
                    disabled={r.skipped}
                    className={`w-full max-w-[180px] rounded border bg-white px-1.5 py-0.5 text-xs ${
                      r.unmatched ? "border-amber-400" : "border-gray-200"
                    } ${r.auto_matched ? "text-emerald-700" : ""}`}
                  >
                    <option value="">— pick a field —</option>
                    {fields.map((f) => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                  </select>
                  {r.auto_matched && r.field_id && !r.is_duplicate && (
                    <p className="mt-0.5 text-[10px] text-emerald-700">auto-matched</p>
                  )}
                  {r.is_duplicate && (
                    <p className="mt-0.5 text-[10px] font-medium text-amber-700">
                      duplicate of an existing analysis (same field + date)
                    </p>
                  )}
                </td>
                <td className="px-2 py-1.5">{r.analysis_date ?? analysisDate ?? "—"}</td>
                <td className="px-2 py-1.5">{r.crop ?? "—"}</td>
                <td className="px-2 py-1.5">{r.lab_name ?? labName ?? "—"}</td>
                <td className="px-2 py-1.5">{Object.keys(r.soil_values).length}</td>
                <td className="px-2 py-1.5">
                  <input
                    type="checkbox"
                    checked={r.skipped}
                    onChange={(e) => onSkipToggle(r.idx, e.target.checked)}
                    className="size-3.5 cursor-pointer"
                  />
                </td>
                <td className="px-2 py-1.5">{issuesCell(r.errors, r.warnings)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Heuristic — pick "soil" or "leaf" from a filename. Returns null when
 * neither pattern matches so the caller falls back to the user's
 * current toggle. Afrikaans + English keywords + a few obvious
 * abbreviations.
 *
 * Examples:
 *   "MFB Trust Blaar 2022.xls"   → "leaf"
 *   "MFB Trust Grond 2022.xls"   → "soil"
 *   "Bemlab Soil Report 2024.pdf" → "soil"
 *   "Foliar Analysis Q3.pdf"     → "leaf"
 *   "Lab report.pdf"             → null
 */
function detectModeFromFilename(name: string): "soil" | "leaf" | null {
  const n = name.toLowerCase();
  if (/\b(blaar|leaf|foliar|petiole|blare)\b/.test(n)) return "leaf";
  if (/\b(grond|soil|bodem|gronde)\b/.test(n)) return "soil";
  return null;
}

/**
 * Canonical form of a block name for matching purposes. Returns "" if
 * the input is empty/whitespace.
 *
 * Normalisations applied:
 *   - lowercase
 *   - strip Latin diacritics (é → e, ô → o, …)
 *   - collapse whitespace + punctuation (no, '-', etc.)
 *   - swap "block" → "blok" (Afrikaans is the canonical form on
 *     Sapling fields per memory + most SA farm conventions)
 *   - drop leading zeros inside numeric segments ("blok 01a" → "blok 1a")
 *
 * Round-trips:
 *   "Blok 1"      → "blok 1"
 *   "Block 1"     → "blok 1"   ← matches
 *   "BLOCK 01"    → "blok 1"   ← matches
 *   "Blok 1A"     → "blok 1a"
 *   "Block 1A"    → "blok 1a"  ← matches
 *   "Laborie A"   → "laborie a"
 *   "Block 15/17" → "blok 15/17" (won't match a single field — needs
 *                  manual reassignment, which is the right answer)
 */
function canonicaliseBlockName(raw: string): string {
  if (!raw) return "";
  let s = raw.normalize("NFD").replace(/[̀-ͯ]/g, "");
  s = s.toLowerCase().trim();
  // English → Afrikaans canonical form (Sapling fields are typically
  // Afrikaans-named, lab files often English; pick one as canonical).
  s = s.replace(/\bblock\b/g, "blok");
  s = s.replace(/\bfield\b/g, "blok");
  s = s.replace(/\blot\b/g, "blok");
  // Collapse multiple whitespace + remove leading zeros from numeric
  // tokens (so "blok 01" matches "blok 1").
  s = s.replace(/\s+/g, " ").replace(/\b0+(\d)/g, "$1");
  return s;
}
