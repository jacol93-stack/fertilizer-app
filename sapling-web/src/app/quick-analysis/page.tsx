"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSessionState, clearSessionGroup } from "@/lib/use-session-state";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/lib/auth-context";
import { ClientSelector, ComboBox } from "@/components/client-selector";
import { api, isFieldAnalysisConflict, type FieldAnalysisConflict } from "@/lib/api";
import { ConflictResolutionDialog, type ConflictResolutionChoice } from "@/components/conflict-resolution-dialog";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
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
  Leaf,
  Loader2,
  Sparkles,
  AlertTriangle,
  RotateCcw,
  Upload,
  PenLine,
  Check,
} from "lucide-react";

import type { CropNorm, Classification, RatioResult, NutrientTarget, ExtractedSample } from "./types";
import { numericSoilValues, importSampleValues } from "./helpers";
import { DocumentUpload } from "./components/document-upload";
import { SamplePicker } from "./components/sample-picker";
import { SoilInputForm } from "./components/soil-input-form";
import { LeafInputForm } from "./components/leaf-input-form";
import { CombinedView } from "./components/combined-view";
import { runAnalysis } from "@/lib/analysis-v2";
import type { ProgrammeArtifact } from "@/lib/types/programme-artifact";
import { ArtifactView } from "@/components/programme-artifact/ArtifactView";

// ── Component ─────────────────────────────────────────────────────────

export default function QuickAnalysisPageWrapper() {
  return (
    <Suspense>
      <QuickAnalysisPage />
    </Suspense>
  );
}

function QuickAnalysisPage() {
  const { isLoading: authLoading } = useAuth();
  const isAdmin = useEffectiveAdmin();
  const router = useRouter();
  const searchParams = useSearchParams();
  const SESSION_KEY = "soil-analysis";

  // ── Step control ────────────────────────────────────────────────
  const [step, setStep] = useState(0); // 0 = Input, 1 = Results

  // ── Analysis type ───────────────────────────────────────────────
  const [analysisType, setAnalysisType] = useState<"soil" | "leaf" | "both">("soil");

  // ── Crop & customer ─────────────────────────────────────────────
  const [crops, setCrops] = useState<CropNorm[]>([]);
  const [selectedCrop, setSelectedCrop] = useSessionState(SESSION_KEY, "selectedCrop", "");
  const [cultivar, setCultivar] = useSessionState(SESSION_KEY, "cultivar", "");
  const [yieldTarget, setYieldTarget] = useSessionState(SESSION_KEY, "yieldTarget", "");
  const [yieldUnit, setYieldUnit] = useSessionState(SESSION_KEY, "yieldUnit", "");
  const [customer, setCustomer] = useSessionState(SESSION_KEY, "customer", "");
  const [farm, setFarm] = useSessionState(SESSION_KEY, "farm", "");
  const [field, setField] = useSessionState(SESSION_KEY, "field", "");
  const [clientId, setClientId] = useSessionState<string | undefined>(SESSION_KEY, "clientId", undefined);
  const [farmId, setFarmId] = useSessionState<string | undefined>(SESSION_KEY, "farmId", undefined);
  const [fieldId, setFieldId] = useSessionState<string | undefined>(SESSION_KEY, "fieldId", undefined);

  // ── Lab & soil values ───────────────────────────────────────────
  const [labName, setLabName] = useSessionState(SESSION_KEY, "labName", "");
  const [analysisDate, setAnalysisDate] = useSessionState(SESSION_KEY, "analysisDate", "");
  const [soilValues, setSoilValues] = useSessionState<Record<string, string>>(SESSION_KEY, "soilValues", {});
  const [leafValues, setLeafValues] = useSessionState<Record<string, string>>(SESSION_KEY, "leafValues", {});

  // ── Extraction state ────────────────────────────────────────────
  const [inputMode, setInputMode] = useState<"manual" | "upload">("manual");
  const [extractedValues, setExtractedValues] = useState<Record<string, number | null> | null>(null);
  const [extractedLabName, setExtractedLabName] = useState<string | null>(null);
  const [extractedSamples, setExtractedSamples] = useState<ExtractedSample[]>([]);
  const [selectedSampleIdx, setSelectedSampleIdx] = useState<number | null>(null);

  // ── Document storage ─────────────────────────────────────────────
  const [sourceDocumentUrl, setSourceDocumentUrl] = useState<string | null>(null);

  // ── Results state ───────────────────────────────────────────────
  const [classifications, setClassifications] = useState<Classification>({});
  const [soilThresholds, setSoilThresholds] = useState<Record<string, { very_low_max: number; low_max: number; optimal_max: number; high_max: number }>>({});
  const [ratios, setRatios] = useState<RatioResult[]>([]);
  const [targets, setTargets] = useState<NutrientTarget[]>([]);
  const [leafResult, setLeafResult] = useState<Record<string, unknown> | null>(null);
  const [leafLoading, setLeafLoading] = useState(false);

  // ── v2 analysis artifact (the rewired engine output) ───────────
  // Step 1 renders this via ArtifactView with mode="analysis" — same
  // visual surface as a full programme minus blends/stage/shopping.
  // Per the project_programme_builder_scope rule, no fertilizer
  // recommendation is produced.
  const [analysisArtifact, setAnalysisArtifact] = useState<ProgrammeArtifact | null>(null);

  // ── Perennial context for age + density scaling ───────────────
  // Captured from the field record when a field is selected so the
  // v2 engine applies the correct age curve. Falls back to manual
  // entry — not surfaced in UI yet (form follow-up).
  const [treeAge, setTreeAge] = useState<number | null>(null);
  const [plantingDate, setPlantingDate] = useState<string | null>(null);
  const [popPerHa, setPopPerHa] = useState<number | null>(null);

  // ── UI state ────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAnalysisId, setSavedAnalysisId] = useState<string | null>(null);
  const [pendingConflicts, setPendingConflicts] = useState<FieldAnalysisConflict[]>([]);
  const [pendingSavePayload, setPendingSavePayload] = useState<Record<string, unknown> | null>(null);

  // ── Pre-fill from URL params (e.g. coming from farm detail page) ──
  useEffect(() => {
    const c = searchParams.get("client");
    const cId = searchParams.get("client_id");
    const f = searchParams.get("farm");
    const fId = searchParams.get("farm_id");
    const fl = searchParams.get("field");
    const flId = searchParams.get("field_id");
    if (cId) {
      if (c) { sessionStorage.setItem(`${SESSION_KEY}:customer`, JSON.stringify(c)); setCustomer(c); }
      sessionStorage.setItem(`${SESSION_KEY}:clientId`, JSON.stringify(cId)); setClientId(cId);
      if (f) { sessionStorage.setItem(`${SESSION_KEY}:farm`, JSON.stringify(f)); setFarm(f); }
      if (fId) { sessionStorage.setItem(`${SESSION_KEY}:farmId`, JSON.stringify(fId)); setFarmId(fId); }
      if (fl) { sessionStorage.setItem(`${SESSION_KEY}:field`, JSON.stringify(fl)); setField(fl); }
      if (flId) { sessionStorage.setItem(`${SESSION_KEY}:fieldId`, JSON.stringify(flId)); setFieldId(flId); }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Load crops ──────────────────────────────────────────────────
  useEffect(() => {
    if (authLoading) return;
    api.get<CropNorm[]>("/api/crop-norms")
      .then(setCrops)
      .catch(() => {
        api.get<CropNorm[]>("/api/crop-norms/admin").then(setCrops).catch(() => {});
      });
  }, [authLoading]);

  // When crop changes, set yield unit
  useEffect(() => {
    if (selectedCrop && crops.length > 0) {
      const crop = crops.find((c) => c.crop === selectedCrop);
      if (crop) setYieldUnit(crop.yield_unit || "t/ha");
    }
  }, [selectedCrop, crops]);

  const getNumericSoilValues = useCallback(
    () => numericSoilValues(soilValues),
    [soilValues]
  );

  // ── Handlers ────────────────────────────────────────────────────

  const handleSampleSelect = (sample: ExtractedSample, averaged?: Record<string, number>) => {
    const values = averaged || sample.values;
    const target = analysisType === "leaf" ? "leaf" : "soil";
    const mapped = importSampleValues(values, target);

    if (target === "leaf") {
      setLeafValues((prev) => ({ ...prev, ...mapped }));
    } else {
      setSoilValues((prev) => ({ ...prev, ...mapped }));
    }

    setExtractedValues(values);
    const idx = averaged ? -1 : extractedSamples.indexOf(sample);
    setSelectedSampleIdx(idx >= 0 ? idx : null);
    if (sample.crop) setSelectedCrop(sample.crop);
    if (sample.cultivar) setCultivar(sample.cultivar);
    setInputMode("manual");
    toast.success(`Imported ${averaged ? "averaged values" : sample.block_name || sample.sample_id || "sample"}`);
  };

  const handleExtracted = (result: {
    department: string | null;
    samples: ExtractedSample[];
    labName: string | null;
    analysisDate: string | null;
    sourceDocumentUrl: string | null;
  }) => {
    if (result.sourceDocumentUrl) setSourceDocumentUrl(result.sourceDocumentUrl);
    if (result.labName) {
      setExtractedLabName(result.labName);
      if (!labName) setLabName(result.labName);
    }
    if (result.analysisDate && !analysisDate) setAnalysisDate(result.analysisDate);

    // Auto-detect report type
    const isLeaf = result.department?.toLowerCase().includes("leaf");
    const isSoil = result.department?.toLowerCase().includes("soil");

    // Merge samples into existing list
    setExtractedSamples((prev) => [...prev, ...result.samples]);

    if (isLeaf && analysisType === "soil") {
      setAnalysisType("leaf");
      toast.info("Leaf analysis detected — switched to Leaf tab");
    } else if (isSoil && analysisType === "leaf") {
      setAnalysisType("soil");
      toast.info("Soil analysis detected — switched to Soil tab");
    }

    // If we now have both soil and leaf extractions
    if ((isLeaf && soilValues && Object.keys(soilValues).length > 0) ||
        (isSoil && leafValues && Object.keys(leafValues).length > 0)) {
      setAnalysisType("both");
    }

    // Auto-import single sample
    if (result.samples.length === 1) {
      const target = isLeaf ? "leaf" : "soil";
      const mapped = importSampleValues(result.samples[0].values, target);
      if (target === "leaf") {
        setLeafValues((prev) => ({ ...prev, ...mapped }));
      } else {
        setSoilValues((prev) => ({ ...prev, ...mapped }));
      }
      setExtractedValues(result.samples[0].values);
      setInputMode("manual");
      toast.success("Extracted values from lab report");
    } else if (result.samples.length > 1) {
      toast.success(`Found ${result.samples.length} samples — select one to import`);
    }
  };

  const handleLearnCorrections = async () => {
    if (!extractedValues || !extractedLabName) return;
    try {
      await api.post("/api/soil/extract/learn", {
        lab_name: extractedLabName,
        original_values: extractedValues,
        corrected_values: getNumericSoilValues(),
      });
      setExtractedValues(null);
      toast.success("Lab template updated with your corrections");
    } catch { /* non-critical */ }
  };

  // Auto-save analysis to the selected farm/field
  const autoSaveAnalysis = async (cls: Classification, rats: RatioResult[], tgts: NutrientTarget[]) => {
    if (!clientId || !farmId) return;
    try {
      const today = new Date().toISOString().slice(0, 10);
      const result = await api.post<{ id: string }>("/api/soil/", {
        client_id: clientId,
        farm_id: farmId,
        field_id: fieldId || null,
        customer: customer || null,
        farm: farm || null,
        field: field || (fieldId ? undefined : `Quick Analysis – ${today}`),
        crop: selectedCrop || null,
        cultivar: cultivar || null,
        yield_target: parseFloat(yieldTarget) || null,
        yield_unit: yieldUnit,
        lab_name: labName,
        analysis_date: analysisDate || today,
        soil_values: getNumericSoilValues(),
        nutrient_targets: tgts.length > 0 ? tgts : null,
        ratio_results: rats,
        classifications: cls,
        source_document_url: sourceDocumentUrl || null,
      });
      setSavedAnalysisId(result.id);
      toast.success("Analysis saved");
    } catch {
      toast.error("Analysis ran but failed to save — you can retry from results");
    }
  };

  // Run soil + leaf analysis through the v2 interpretation engine.
  //
  // Replaces the legacy /api/soil/run + /api/leaf/classify pair with
  // a single /api/analysis/v2/run call. The v2 path automatically
  // pulls in everything migration 080/081 seeded (citrus + avo +
  // mac sufficiency + leaf bands), the Phase A age-factor scaling,
  // soil-factor reasoning (Al / SAR / antagonisms), foliar trigger
  // detection, and current-stage detection — all of which the legacy
  // path missed.
  //
  // Underlying soil + leaf records still persist via /api/soil/ for
  // downstream wizard/quote use; the analysis report itself is
  // ephemeral.
  const handleAnalyze = async () => {
    if (!clientId || !farmId) {
      toast.error("Please select a client and farm first");
      return;
    }
    if (!selectedCrop) {
      toast.error("Pick a crop — needed to score soil/leaf against the right bands");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Build leaf_values dict (only entries with parseable positive values)
      const leafNum: Record<string, number> = {};
      for (const [k, v] of Object.entries(leafValues)) {
        const n = parseFloat(v);
        if (n > 0) leafNum[k] = n;
      }
      const hasLeaf = Object.keys(leafNum).length > 0;
      const yieldTargetNum = parseFloat(yieldTarget);

      // numericSoilValues emits null for empty cells; the engine only
      // wants populated entries (nulls confuse the soil-factor reasoner
      // that uses .get(...) lookups).
      const soilNumRaw = getNumericSoilValues();
      const soilNum: Record<string, number> = {};
      for (const [k, v] of Object.entries(soilNumRaw)) {
        if (typeof v === "number" && Number.isFinite(v)) soilNum[k] = v;
      }

      const { artifact } = await runAnalysis({
        crop: selectedCrop,
        prepared_for: customer || "Quick Analysis",
        client_name: customer || null,
        farm_name: farm || null,
        planting_date: plantingDate,
        blocks: [
          {
            block_id: fieldId || "manual",
            block_name: field || "Quick Analysis",
            block_area_ha: 1.0, // placeholder — analysis is per-ha so area=1 is fine
            soil_parameters: soilNum,
            leaf_values: hasLeaf ? leafNum : null,
            yield_target_per_ha: Number.isFinite(yieldTargetNum) && yieldTargetNum > 0
              ? yieldTargetNum
              : null,
            tree_age: treeAge,
            pop_per_ha: popPerHa,
            lab_name: labName || null,
            sample_date: analysisDate || null,
          },
        ],
      });
      setAnalysisArtifact(artifact);

      // Auto-save the underlying soil/leaf record (legacy persistence
      // path stays — the wizard, quotes, and Season Tracker still
      // consume those rows).
      await autoSaveAnalysis(
        {} as Classification, // legacy fields no longer drive UI; pass empty
        [],
        [],
      );

      setStep(1);

      if (extractedValues && extractedLabName) handleLearnCorrections();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  // Run leaf classification
  const runLeafClassification = async () => {
    const values: Record<string, number> = {};
    for (const [k, v] of Object.entries(leafValues)) {
      const n = parseFloat(v);
      if (n > 0) values[k] = n;
    }
    if (Object.keys(values).length === 0) return;

    setLeafLoading(true);
    try {
      const res = await api.post<Record<string, unknown>>("/api/leaf/classify", {
        crop: selectedCrop || null,
        values,
      });
      setLeafResult(res);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Leaf classification failed");
    } finally {
      setLeafLoading(false);
    }
  };

  // Leaf-only analysis
  const handleLeafAnalyze = async () => {
    if (!clientId || !farmId) {
      toast.error("Please select a client and farm first");
      return;
    }
    const values: Record<string, number> = {};
    for (const [k, v] of Object.entries(leafValues)) {
      const n = parseFloat(v);
      if (n > 0) values[k] = n;
    }
    if (Object.keys(values).length === 0) {
      toast.error("Enter at least one element value");
      return;
    }
    setLeafLoading(true);
    setLeafResult(null);
    try {
      const res = await api.post<Record<string, unknown>>("/api/leaf/classify", {
        crop: selectedCrop || null,
        values,
      });
      setLeafResult(res);
      // Auto-save (leaf-only saves with empty soil data)
      await autoSaveAnalysis({}, [], []);
      setStep(1);
      toast.success("Leaf analysis classified");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Classification failed");
    } finally {
      setLeafLoading(false);
    }
  };

  // Save analysis
  const handleSaveAnalysis = async () => {
    if (!clientId || !farmId) {
      toast.error("Please select a client and farm before saving");
      return;
    }
    if (savedAnalysisId) {
      if (!confirm("This analysis has already been saved. Save again as a new record?")) return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = {
        client_id: clientId || null,
        farm_id: farmId || null,
        field_id: fieldId || null,
        customer: customer || null,
        farm: farm || null,
        field: field || null,
        crop: selectedCrop || null,
        cultivar: cultivar || null,
        yield_target: parseFloat(yieldTarget) || null,
        yield_unit: yieldUnit,
        lab_name: labName,
        analysis_date: analysisDate || null,
        soil_values: getNumericSoilValues(),
        nutrient_targets: targets.length > 0 ? targets : null,
        ratio_results: ratios,
        classifications,
      };

      try {
        const result = await api.post<{ id: string }>("/api/soil/", payload);
        setSavedAnalysisId(result.id);
        toast.success("Soil analysis saved");
      } catch (err) {
        const conflicts = isFieldAnalysisConflict(err);
        if (!conflicts) throw err;
        // Defer to the modal — handleConflictResolved re-posts.
        setPendingSavePayload(payload);
        setPendingConflicts(conflicts);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConflictResolved = async (choice: ConflictResolutionChoice) => {
    const payload = pendingSavePayload;
    setPendingConflicts([]);
    setPendingSavePayload(null);
    if (!payload) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.post<{ id: string }>("/api/soil/", {
        ...payload,
        conflict_resolution: choice,
      });
      setSavedAnalysisId(result.id);
      toast.success(choice === "merge_as_composite" ? "Merged into existing analysis" : "Soil analysis saved");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConflictCancelled = () => {
    setPendingConflicts([]);
    setPendingSavePayload(null);
    toast.info("Save cancelled — no changes made");
  };

  // Build a Programme — analysis is already auto-saved, just navigate
  const handleBuildProgramme = async () => {
    const params = new URLSearchParams({ new: "true" });
    if (savedAnalysisId) params.set("analysis_id", savedAnalysisId);
    if (clientId) params.set("client_id", clientId);
    if (farmId) params.set("farm_id", farmId);
    router.push(`/season-manager?${params.toString()}`);
  };

  // ── Tab config ──────────────────────────────────────────────────
  const tabs = ["Input", "Diagnostic Results"];

  const hasSoilData = Object.keys(classifications).length > 0;
  const hasLeafData = leafResult != null;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
              <Leaf className="size-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Quick Analysis</h1>
              <p className="text-sm text-[var(--sapling-medium-grey)]">
                Classify soil and leaf samples — quick diagnostic reports
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (!confirm("Clear all form data and start fresh?")) return;
              clearSessionGroup(SESSION_KEY);
              window.location.reload();
            }}
          >
            <RotateCcw className="size-3.5" data-icon="inline-start" />
            Reset
          </Button>
        </div>

        {/* Analysis type toggle */}
        <div className="mb-6 flex rounded-lg bg-muted p-1">
          {([
            { key: "soil" as const, label: "Soil Analysis", icon: Leaf },
            { key: "leaf" as const, label: "Leaf Analysis", icon: Sparkles },
            { key: "both" as const, label: "Soil + Leaf", icon: Leaf },
          ]).map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setAnalysisType(t.key)}
              className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                analysisType === t.key
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <t.icon className="size-4" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab navigation */}
        <div className="mb-6 flex gap-1 rounded-lg bg-muted p-1">
          {tabs.map((tab, i) => (
            <button
              key={tab}
              onClick={() => i <= step && setStep(i)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                step === i
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : i <= step
                    ? "cursor-pointer text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
                    : "cursor-not-allowed text-muted-foreground/50"
              }`}
              disabled={i > step}
            >
              {tab}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button onClick={() => setError(null)} className="ml-2 font-medium underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Multi-sample picker */}
        {extractedSamples.length > 1 && step === 0 && (
          <div className="mb-6">
            <SamplePicker
              samples={extractedSamples}
              onSelect={handleSampleSelect}
              selectedIdx={selectedSampleIdx}
            />
          </div>
        )}

        {/* ═══════════ STEP 0: INPUT ═══════════ */}
        <div className="space-y-6" style={{ display: step === 0 ? undefined : "none" }}>
            {/* Customer & crop info */}
            <Card className="overflow-visible">
              <CardHeader>
                <CardTitle>Crop & Customer Info</CardTitle>
                <CardDescription>
                  Crop is optional — analysis works without it, but crop-specific thresholds improve accuracy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5 overflow-visible">
                <ClientSelector
                  onSelect={async (sel) => {
                    setCustomer(sel.client_name);
                    setFarm(sel.farm_name);
                    setField(sel.field_name);
                    setClientId(sel.client_id);
                    setFarmId(sel.farm_id);
                    setFieldId(sel.field_id);
                    if (sel.field_id) {
                      try {
                        // Fetch field record to auto-populate crop data
                        const fieldData = await api.get<Record<string, unknown>>(
                          `/api/clients/fields/${sel.field_id}`
                        );
                        if (fieldData) {
                          if (fieldData.crop && !selectedCrop) setSelectedCrop(String(fieldData.crop));
                          if (fieldData.cultivar && !cultivar) setCultivar(String(fieldData.cultivar));
                          if (fieldData.yield_target && !yieldTarget) setYieldTarget(String(fieldData.yield_target));
                          if (fieldData.yield_unit) setYieldUnit(String(fieldData.yield_unit));
                          // Perennial context for v2 engine — drives
                          // age + density scaling so a young block
                          // isn't read against full-bearing norms.
                          setTreeAge(typeof fieldData.tree_age === "number" ? fieldData.tree_age : null);
                          setPlantingDate(typeof fieldData.planting_date === "string" ? fieldData.planting_date : null);
                          setPopPerHa(typeof fieldData.pop_per_ha === "number" ? fieldData.pop_per_ha : null);

                          // Auto-populate from linked analysis
                          if (fieldData.latest_analysis_id) {
                            try {
                              const analysis = await api.get<Record<string, unknown>>(
                                `/api/soil/${fieldData.latest_analysis_id}`
                              );
                              if (analysis) {
                                let hasSoil = false;
                                let hasLeaf = false;
                                if (analysis.soil_values && typeof analysis.soil_values === "object") {
                                  const sv: Record<string, string> = {};
                                  for (const [k, v] of Object.entries(analysis.soil_values as Record<string, unknown>)) {
                                    if (v != null) sv[k] = String(v);
                                  }
                                  if (Object.keys(sv).length > 0) { setSoilValues(sv); hasSoil = true; }
                                }
                                if (analysis.leaf_values && typeof analysis.leaf_values === "object") {
                                  const lv: Record<string, string> = {};
                                  for (const [k, v] of Object.entries(analysis.leaf_values as Record<string, unknown>)) {
                                    if (v != null) lv[k] = String(v);
                                  }
                                  if (Object.keys(lv).length > 0) { setLeafValues(lv); hasLeaf = true; }
                                }
                                if (hasSoil && hasLeaf) setAnalysisType("both");
                                else if (hasLeaf) setAnalysisType("leaf");
                                if (analysis.lab_name && !labName) setLabName(String(analysis.lab_name));
                                if (analysis.analysis_date && !analysisDate) setAnalysisDate(String(analysis.analysis_date));
                                toast.success("Loaded linked analysis for this field");
                              }
                            } catch { /* best-effort — analysis may have been deleted */ }
                          }
                        }
                      } catch { /* best-effort */ }
                    }
                  }}
                  initialClient={customer}
                  initialFarm={farm}
                  initialField={field}
                />

                <div className="grid gap-4 sm:grid-cols-3">
                  <ComboBox
                    label="Crop (optional)"
                    placeholder="Select or type crop..."
                    items={crops.map((c) => ({ id: c.id || c.crop, name: c.crop, type: c.type, yield_unit: c.yield_unit, default_yield: c.default_yield })) as unknown as Record<string, unknown>[]}
                    value={selectedCrop}
                    onChange={(val) => {
                      if (val !== selectedCrop) {
                        setSelectedCrop(val);
                        setCultivar("");
                        setYieldTarget("");
                      }
                    }}
                    onSelect={(item) => {
                      const newCrop = String(item.name);
                      if (newCrop !== selectedCrop) {
                        setCultivar("");
                        setYieldTarget(item.default_yield ? String(item.default_yield) : "");
                      }
                      setSelectedCrop(newCrop);
                      setYieldUnit(item.yield_unit ? String(item.yield_unit) : "");
                    }}
                    secondaryKey="type"
                  />
                  <div className="space-y-1.5">
                    <Label htmlFor="cultivar">Cultivar</Label>
                    <Input
                      id="cultivar"
                      value={cultivar}
                      onChange={(e) => setCultivar(e.target.value)}
                      placeholder="e.g. Hass, PAN 5R-589R"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="yieldTarget">Yield Target ({yieldUnit || "t/ha"})</Label>
                    <Input
                      id="yieldTarget"
                      type="number"
                      value={yieldTarget}
                      onChange={(e) => setYieldTarget(e.target.value)}
                      placeholder="e.g. 12"
                    />
                  </div>
                </div>

                {/* Custom norms banner */}
                {selectedCrop && crops.find((c) => c.crop === selectedCrop && c.is_overridden) && (
                  <div className="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
                    <AlertTriangle className="size-4 shrink-0" />
                    <span>
                      <strong>{selectedCrop}</strong> is using your custom crop norms.{" "}
                      <a href="/profile" className="underline hover:text-orange-900">View overrides</a>
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Input mode toggle */}
            <Card>
              <CardHeader>
                <CardTitle>
                  {analysisType === "leaf" ? "Leaf Values" : analysisType === "both" ? "Soil & Leaf Values" : "Soil Values"}
                </CardTitle>
                <CardDescription>Upload lab reports or enter values manually</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex rounded-lg bg-muted p-1">
                  <button
                    type="button"
                    onClick={() => setInputMode("upload")}
                    className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      inputMode === "upload"
                        ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Upload className="size-4" />
                    Upload Report
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputMode("manual")}
                    className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      inputMode === "manual"
                        ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <PenLine className="size-4" />
                    Enter Manually
                  </button>
                </div>

                {inputMode === "upload" && (
                  <DocumentUpload
                    labNameHint={labName || undefined}
                    clientId={clientId || undefined}
                    onExtracted={handleExtracted}
                    onError={(msg) => setError(msg)}
                  />
                )}
              </CardContent>
            </Card>

            {/* Extracted values notification */}
            {extractedValues && (
              <div className="flex items-center justify-between rounded-lg border border-green-200 bg-green-50 px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-green-800">
                  <Check className="size-4" />
                  Values extracted from {extractedLabName || "lab report"} — review and correct below
                </div>
                <Button size="sm" variant="outline" onClick={handleLearnCorrections} className="text-xs">
                  Confirm Corrections
                </Button>
              </div>
            )}

            {/* Manual input forms */}
            {(analysisType === "soil" || analysisType === "both") && (
              <SoilInputForm
                soilValues={soilValues}
                onChange={setSoilValues}
                labName={labName}
                onLabNameChange={setLabName}
                analysisDate={analysisDate}
                onAnalysisDateChange={setAnalysisDate}
              />
            )}

            {(analysisType === "leaf" || analysisType === "both") && (
              <LeafInputForm leafValues={leafValues} onChange={setLeafValues} />
            )}

            {/* Run Analysis button */}
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {!clientId || !farmId
                  ? "Select a client and farm above to run and save an analysis"
                  : fieldId
                    ? "Analysis will be saved and linked to the selected field"
                    : "Analysis will be saved to the farm (unlinked)"}
              </p>
              {analysisType === "leaf" ? (
                <Button
                  size="lg"
                  onClick={handleLeafAnalyze}
                  disabled={leafLoading || !clientId || !farmId}
                  className="h-12 bg-[var(--sapling-orange)] text-base font-semibold text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  {leafLoading ? <Loader2 className="size-5 animate-spin" /> : <Sparkles className="size-5" />}
                  {leafLoading ? "Classifying..." : "Classify Leaf Analysis"}
                </Button>
              ) : (
                <Button
                  onClick={handleAnalyze}
                  disabled={loading || !clientId || !farmId}
                  className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  {loading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                  Run Analysis
                </Button>
              )}
            </div>
          </div>

        {/* ═══════════ STEP 1: DIAGNOSTIC RESULTS (v2 engine) ═══════ */}
        {/* The v2 analysis pipeline produces a ProgrammeArtifact-shaped
            report with empty blends/stage_schedules/shopping_list.
            ArtifactView with mode="analysis" hides those sections so
            we get the same visual surface as a full programme minus
            the fertilizer recommendation. */}
        {step === 1 && analysisArtifact && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Button variant="outline" onClick={() => setStep(0)}>
                ← Back to inputs
              </Button>
              {savedAnalysisId && (
                <Button
                  onClick={handleBuildProgramme}
                  className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  Build full programme from this analysis →
                </Button>
              )}
            </div>
            <ArtifactView artifact={analysisArtifact} mode="analysis" />
          </div>
        )}
      </div>
      <ConflictResolutionDialog
        open={pendingConflicts.length > 0}
        conflicts={pendingConflicts}
        onResolve={handleConflictResolved}
        onCancel={handleConflictCancelled}
      />
    </AppShell>
  );
}
