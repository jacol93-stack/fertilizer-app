"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ClientSelector } from "@/components/client-selector";
import { useAuth } from "@/lib/auth-context";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { ChevronRight, ChevronLeft, Loader2, Leaf, Check, AlertTriangle } from "lucide-react";

import { FieldPicker } from "@/components/season-manager/field-picker";
import { ScheduleReview, type BlockInfo, type UserApplication } from "@/components/season-manager/schedule-review";
import { BlendGroups, type BlendGroupData } from "@/components/season-manager/blend-groups";
import type { Programme, Block, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { emptyBlock } from "@/lib/season-constants";
import type { MethodAvailability } from "@/lib/types/programme-artifact";
import {
  wizardStateToBuildRequest,
  defaultMethodAvailability,
  WizardAdapterError,
  type SoilAnalysisMeta,
} from "@/lib/adapters/wizard-to-v2";
import { buildProgramme } from "@/lib/programmes-v2";

export default function SeasonBuilderPageWrapper() {
  return (
    <Suspense>
      <SeasonBuilderPage />
    </Suspense>
  );
}

const STEPS = ["Client & Farm", "Blocks", "Schedule", "Blends", "Review"];

function SeasonBuilderPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const handoffProcessed = useRef(false);
  const isAdmin = useEffectiveAdmin();

  const analysisId = searchParams.get("analysis_id");
  const urlClientId = searchParams.get("client_id");
  const urlFarmId = searchParams.get("farm_id");
  const urlClientName = searchParams.get("client");
  const urlFarmName = searchParams.get("farm");

  // ── Wizard state ────────────────────────────────────────────────
  const [wizardStep, setWizardStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  // ── Data ────────────────────────────────────────────────────────
  const [clientId, setClientId] = useState<string>(urlClientId || "");
  const [farmId, setFarmId] = useState<string>(urlFarmId || "");
  const [clientName, setClientName] = useState(urlClientName || "");
  const [farmName, setFarmName] = useState(urlFarmName || "");
  const [programmeName, setProgrammeName] = useState("");
  const [season, setSeason] = useState("");
  const [blocks, setBlocks] = useState<Omit<Block, "id">[]>([emptyBlock()]);

  // Programme ID (created when advancing past step 2)
  const [programmeId, setProgrammeId] = useState<string | null>(null);

  // Schedule data (from preview-schedule)
  const [blockInfoData, setBlockInfoData] = useState<BlockInfo[]>([]);
  const [userApplications, setUserApplications] = useState<UserApplication[]>([]);
  const [plantingMonths, setPlantingMonths] = useState<Record<string, number>>({});
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [unplanableBlocks, setUnplanableBlocks] = useState<Array<{ block_id: string; block_name: string; reason: string; crop?: string }>>([]);

  // Blend groups data (from generate)
  const [blendGroupsData, setBlendGroupsData] = useState<BlendGroupData[]>([]);

  // Method availability — captured on step 0, consumed by "Build Artifact"
  // on the Review step. Not used by the legacy generate flow.
  const [methodAvailability, setMethodAvailability] = useState<MethodAvailability>(
    defaultMethodAvailability(),
  );
  const [buildingArtifact, setBuildingArtifact] = useState(false);

  // Reference data
  const [crops, setCrops] = useState<CropNorm[]>([]);
  const [availableAnalyses, setAvailableAnalyses] = useState<SoilAnalysis[]>([]);
  const [clientFarms, setClientFarms] = useState<Array<{ id: string; name: string }>>([]);

  // ── Resolve URL params (client/farm IDs → names + blocks) ───────
  useEffect(() => {
    if (!urlClientId || analysisId) return;
    (async () => {
      try {
        // Resolve client name
        const clients = await api.getAll<{ id: string; name: string }>("/api/clients");
        const client = clients.find((c) => c.id === urlClientId);
        if (client) {
          setClientName(client.name);
          // Load all farms for this client (for multi-farm block adding)
          const farms = await api.get<Array<{ id: string; name: string }>>(`/api/clients/${urlClientId}/farms`);
          setClientFarms(farms || []);

          if (urlFarmId) {
            const farm = farms.find((f) => f.id === urlFarmId);
            if (farm) setFarmName(farm.name);
          }
        }
      } catch {}
    })();
  }, [urlClientId, urlFarmId, analysisId]);

  // ── Load crops ──────────────────────────────────────────────────
  useEffect(() => {
    api.get<CropNorm[]>("/api/crop-norms")
      .then(setCrops)
      .catch(() => {
        api.get<CropNorm[]>("/api/crop-norms/admin").then(setCrops).catch(() => {});
      });
  }, []);

  // Load analyses and farms when client selected
  useEffect(() => {
    if (clientId) {
      api.getAll<SoilAnalysis>(`/api/soil?client_id=${clientId}`)
        .then(setAvailableAnalyses)
        .catch(() => {});
      api.get<Array<{ id: string; name: string }>>(`/api/clients/${clientId}/farms`)
        .then(setClientFarms)
        .catch(() => {});
    }
  }, [clientId]);

  // FieldPicker (step 1) handles loading + auto-selection of the farm's
  // fields into blocks. No wizard-level useEffect needed.

  // Auto-generate programme name + season. Name is just client/farm —
  // the season already lives in its own field, so duplicating it in the
  // name leaves the two out of sync when the agent edits either.
  useEffect(() => {
    if (clientName && !programmeName) {
      setProgrammeName(farmName ? `${clientName} — ${farmName}` : clientName);
    }
    if (!season) {
      const year = new Date().getFullYear();
      setSeason(`${year}/${year + 1}`);
    }
  }, [clientName, farmName]);

  // Handle handoff from Quick Analysis
  useEffect(() => {
    if (handoffProcessed.current || !analysisId) return;
    handoffProcessed.current = true;
    (async () => {
      try {
        const analysis = await api.get<Record<string, unknown>>(`/api/soil/${analysisId}`);
        if (analysis.client_id) setClientId(analysis.client_id as string);
        if (analysis.farm_id) setFarmId(analysis.farm_id as string);
        if (analysis.customer) setClientName(String(analysis.customer));
        if (analysis.farm) setFarmName(String(analysis.farm));
        setBlocks([{
          name: analysis.field ? String(analysis.field) : "Block 1",
          area_ha: null,
          crop: analysis.crop ? String(analysis.crop) : "",
          cultivar: analysis.cultivar ? String(analysis.cultivar) : "",
          yield_target: analysis.yield_target ? Number(analysis.yield_target) : null,
          yield_unit: analysis.yield_unit ? String(analysis.yield_unit) : "",
          tree_age: null,
          pop_per_ha: analysis.pop_per_ha ? Number(analysis.pop_per_ha) : null,
          soil_analysis_id: analysisId,
          notes: "",
        }]);
        setWizardStep(1);
        toast.info("Pre-filled from soil analysis — review blocks and continue");
      } catch {
        toast.error("Could not load analysis");
      }
    })();
  }, [analysisId]);

  // ── Step transitions ────────────────────────────────────────────

  // Step 1→2: Create programme (if not yet created), then preview schedule
  const handleAdvanceToSchedule = async () => {
    if (!clientId) {
      toast.error("Please select a client");
      return;
    }

    setSaving(true);
    setScheduleError(null);
    try {
      // Create programme if needed
      let pid = programmeId;
      if (!pid) {
        const validBlocks = blocks.filter((b) => b.crop && b.name);
        const result = await api.post<Programme>("/api/programmes", {
          client_id: clientId || null,
          farm_id: farmId || null,
          name: programmeName,
          season,
          status: "draft",
          blocks: validBlocks.map((b) => ({
            name: b.name,
            area_ha: b.area_ha || null,
            crop: b.crop,
            cultivar: b.cultivar || null,
            yield_target: b.yield_target || null,
            yield_unit: b.yield_unit || null,
            tree_age: b.tree_age || null,
            pop_per_ha: b.pop_per_ha || null,
            soil_analysis_id: b.soil_analysis_id || null,
          })),
        });
        pid = result.id;
        setProgrammeId(pid);
      }

      // Preview schedule — get block info with growth stages
      const preview = await api.post<{
        schedule: unknown[];
        block_info: BlockInfo[];
        unplanable_blocks?: Array<{ block_id: string; block_name: string; reason: string; crop?: string }>;
      }>(`/api/programmes/${pid}/preview-schedule`);
      setBlockInfoData(preview.block_info);
      setUnplanableBlocks(preview.unplanable_blocks || []);
      setUserApplications([]);
      if (preview.unplanable_blocks && preview.unplanable_blocks.length > 0) {
        toast.info(`${preview.unplanable_blocks.length} block${preview.unplanable_blocks.length !== 1 ? "s" : ""} skipped — see warning`);
      }
      setWizardStep(2);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed";
      setScheduleError(msg);
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  // Step 2→3: Generate blends
  const handleAdvanceToBlends = async () => {
    if (!programmeId) return;
    setGenerating(true);
    try {
      const generateBody: Record<string, unknown> = {};
      if (userApplications.length > 0) generateBody.applications = userApplications;
      if (Object.keys(plantingMonths).length > 0) {
        generateBody.planting_months = Object.entries(plantingMonths).map(([block_id, month]) => ({ block_id, month }));
      }
      const result = await api.post<Record<string, unknown>>(
        `/api/programmes/${programmeId}/generate`,
        generateBody
      );

      // Build blend group display data from the programme detail
      const prog = await api.get<Record<string, unknown>>(`/api/programmes/${programmeId}`);
      const blends = (prog.blends || []) as Array<Record<string, unknown>>;
      const progBlocks = (prog.blocks || []) as Array<Record<string, unknown>>;

      // Group blends by blend_group — each saved blend row now carries
      // its own recipe/notation/rate (one row per application), so the
      // aggregator pushes a full application record per blend, not a
      // single per-group summary.
      const FOLIAR_METHODS = new Set(["foliar", "foliar_spray"]);
      const groupMap = new Map<string, BlendGroupData>();
      for (const blend of blends) {
        const group = String(blend.blend_group || "A");
        if (!groupMap.has(group)) {
          const groupBlocks = progBlocks.filter((b) => b.blend_group === group);
          groupMap.set(group, {
            group,
            crops: [...new Set(groupBlocks.map((b) => String(b.crop)))],
            block_names: groupBlocks.map((b) => String(b.name)),
            total_area_ha: groupBlocks.reduce((s, b) => s + (Number(b.area_ha) || 0), 0),
            applications: [],
          });
        }
        const method = String(blend.method || "broadcast");
        groupMap.get(group)!.applications.push({
          stage_name: String(blend.stage_name || ""),
          month: Number(blend.application_month) || 1,
          method,
          sa_notation: String(blend.sa_notation || ""),
          rate_kg_ha: Number(blend.rate_kg_ha) || 0,
          cost_per_ton: blend.blend_cost_per_ton != null ? Number(blend.blend_cost_per_ton) : undefined,
          recipe: (blend.blend_recipe || []) as NonNullable<BlendGroupData["applications"][number]["recipe"]>,
          is_foliar: FOLIAR_METHODS.has(method),
        });
      }

      setBlendGroupsData(Array.from(groupMap.values()));
      setWizardStep(3);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  // Build programme artifact via the new v2 engine. Runs alongside the
  // legacy generate flow — needs plantingMonths (step 2) + blockInfoData
  // so it can resolve server block_ids back to block names.
  const handleBuildArtifact = async () => {
    try {
      setBuildingArtifact(true);

      // Pre-flight — Build Artifact sits on the last wizard step, so
      // all of these should already be populated. Guard with specific
      // messages so the agronomist doesn't stare at a generic error
      // when they skipped a step.
      const validBlocks = blocks.filter((b) => b.crop && b.name && b.soil_analysis_id);
      if (validBlocks.length === 0) {
        toast.error(
          "No blocks have a soil analysis linked. Go back to Step 1 and link one.",
        );
        return;
      }
      if (blockInfoData.length === 0) {
        toast.error(
          "Schedule hasn't been generated. Go back to Step 2 (Schedule) first.",
        );
        return;
      }
      if (Object.keys(plantingMonths).length === 0) {
        toast.error(
          "No planting months set. Set one on Step 2 (Schedule) for each block.",
        );
        return;
      }

      // Build block_id → block_name from preview-schedule output, so we
      // can project plantingMonths (keyed by server block_id) onto names.
      const nameByBlockId = new Map(blockInfoData.map((bi) => [bi.block_id, bi.block_name]));
      const plantingMonthByBlockName: Record<string, number> = {};
      for (const [bid, month] of Object.entries(plantingMonths)) {
        const name = nameByBlockId.get(bid);
        if (name) plantingMonthByBlockName[name] = month;
      }

      // Fetch soil_values per analysis (list view doesn't include them).
      // A single failing fetch shouldn't break the whole build — wrap
      // each in a .catch so one bad analysis becomes a skipped block
      // (via empty soil_values), not a hard error.
      const analysisIds = Array.from(
        new Set(validBlocks.map((b) => b.soil_analysis_id!).filter(Boolean)),
      );
      const analyses = await Promise.all(
        analysisIds.map(async (id) => {
          try {
            const row = await api.get<Record<string, unknown>>(`/api/soil/${id}`);
            return { id, row };
          } catch (err) {
            console.error(`Failed to fetch soil analysis ${id}`, err);
            return { id, row: {} as Record<string, unknown> };
          }
        }),
      );
      const soilValuesByAnalysisId: Record<string, Record<string, number>> = {};
      const soilMetaByAnalysisId: Record<string, SoilAnalysisMeta> = {};
      for (const { id, row } of analyses) {
        const sv = (row.soil_values as Record<string, number> | null) ?? {};
        soilValuesByAnalysisId[id] = sv;
        soilMetaByAnalysisId[id] = {
          id,
          lab_name: (row.lab_name as string | null) ?? null,
          analysis_date: (row.analysis_date as string | null) ?? null,
        };
      }

      // Pass ALL named blocks (not just those with soil data) so the
      // adapter can split them into planned vs skipped; the skipped set
      // flows to the artifact as OutstandingItems instead of being
      // silently dropped.
      const namedBlocks = blocks.filter((b) => b.crop && b.name);
      const { request, skippedBlocks } = wizardStateToBuildRequest({
        clientName,
        farmName,
        preparedFor: clientName,
        season,
        clientId: clientId || null,
        blocks: namedBlocks.map((b) => ({
          name: b.name,
          area_ha: b.area_ha,
          crop: b.crop,
          cultivar: b.cultivar,
          yield_target: b.yield_target,
          yield_unit: b.yield_unit,
          soil_analysis_id: b.soil_analysis_id,
        })),
        plantingMonthByBlockName,
        soilValuesByAnalysisId,
        soilMetaByAnalysisId,
        methodAvailability,
      });

      const response = await buildProgramme(request);
      if (skippedBlocks.length > 0) {
        toast.warning(
          `${skippedBlocks.length} block${skippedBlocks.length !== 1 ? "s" : ""} not planned (no soil analysis) — see Outstanding Items`,
        );
      } else {
        toast.success("Programme generated");
      }
      router.push(`/season-manager/artifact/${response.id}`);
    } catch (e) {
      // Always log — toast messages are short; console gets the raw
      // exception for actual debugging.
      console.error("handleBuildArtifact failed", e);
      if (e instanceof WizardAdapterError) {
        toast.error(e.message);
      } else if (e instanceof Error) {
        toast.error(`Build failed: ${e.message}`);
      } else {
        toast.error("Build failed (unknown error — check console)");
      }
    } finally {
      setBuildingArtifact(false);
    }
  };

  // Final: navigate to programme detail
  const handleFinish = (activate: boolean) => {
    if (!programmeId) return;
    if (activate) {
      api.patch(`/api/programmes/${programmeId}`, { status: "active" })
        .then(() => {
          toast.success("Programme activated");
          router.push(`/season-manager/${programmeId}`);
        })
        .catch(() => {
          toast.error("Failed to activate");
          router.push(`/season-manager/${programmeId}`);
        });
    } else {
      toast.success("Programme saved as draft");
      router.push(`/season-manager/${programmeId}`);
    }
  };

  // ── Validation ──────────────────────────────────────────────────
  const canNext = () => {
    if (wizardStep === 0) return !!programmeName && !!clientId;
    if (wizardStep === 1) return blocks.some((b) => b.crop && b.name && b.soil_analysis_id);
    if (wizardStep === 2) return userApplications.length > 0;
    if (wizardStep === 3) return blendGroupsData.length > 0;
    return true;
  };

  const handleNext = () => {
    if (wizardStep === 1) {
      // Blocks → Schedule: need to create programme + preview
      handleAdvanceToSchedule();
    } else if (wizardStep === 2) {
      // Schedule → Blends: need to generate
      handleAdvanceToBlends();
    } else {
      setWizardStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    if (wizardStep === 0) {
      router.push("/season-manager");
    } else {
      setWizardStep((s) => s - 1);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <Leaf className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Build New Programme</h1>
            <p className="text-sm text-[var(--sapling-medium-grey)]">
              Define blocks, review the feeding schedule, and generate optimized blends
            </p>
          </div>
        </div>

        {/* Step indicator */}
        <div className="mb-6 flex gap-1 rounded-lg bg-muted p-1">
          {STEPS.map((s, i) => (
            <button
              key={s}
              onClick={() => i <= wizardStep && setWizardStep(i)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                wizardStep === i
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : i <= wizardStep
                    ? "cursor-pointer text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
                    : "cursor-not-allowed text-muted-foreground/50"
              }`}
              disabled={i > wizardStep}
            >
              {i < wizardStep && <Check className="mr-1 inline size-3 text-green-600" />}
              {s}
            </button>
          ))}
        </div>

        <Card className="overflow-visible">
          <CardContent className="pt-6 overflow-visible">
            {/* ══ Step 0: Client & Farm ══ */}
            {wizardStep === 0 && (
              <div className="space-y-5">
                <ClientSelector
                  onSelect={(sel) => {
                    setClientName(sel.client_name);
                    setFarmName(sel.farm_name);
                    setClientId(sel.client_id || "");
                    setFarmId(sel.farm_id || "");
                  }}
                  initialClient={clientName}
                  initialFarm={farmName}
                  showField={false}
                />
                <p className="-mt-1 text-xs text-muted-foreground">
                  A programme covers a whole farm. Pick the specific fields (blocks) in the next step.
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Programme Name *</Label>
                    <Input
                      value={programmeName}
                      onChange={(e) => setProgrammeName(e.target.value)}
                      placeholder="e.g. Farm ABC"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Season</Label>
                    <Input
                      value={season}
                      onChange={(e) => setSeason(e.target.value)}
                      placeholder="e.g. 2026/2027"
                    />
                  </div>
                </div>

                <div className="mt-2 rounded-lg border border-dashed border-gray-300 p-4">
                  <Label className="mb-2 block text-sm font-medium">
                    Application methods available on this farm
                  </Label>
                  <p className="mb-3 text-xs text-muted-foreground">
                    The programme will route nutrients through the methods you tick
                    here — fertigation, foliar, granular broadcast, etc.
                  </p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {([
                      ["has_drip", "Drip fertigation"],
                      ["has_pivot", "Pivot fertigation"],
                      ["has_sprinkler", "Sprinkler fertigation"],
                      ["has_foliar_sprayer", "Foliar sprayer"],
                      ["has_granular_spreader", "Granular spreader"],
                      ["has_fertigation_injectors", "Fertigation injectors (A/B)"],
                      ["has_seed_treatment", "Seed treatment"],
                    ] as Array<[keyof MethodAvailability, string]>).map(([key, label]) => (
                      <label key={key} className="flex cursor-pointer items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={methodAvailability[key]}
                          onChange={(e) =>
                            setMethodAvailability((m) => ({ ...m, [key]: e.target.checked }))
                          }
                          className="size-4 rounded border-gray-300 text-[var(--sapling-orange)] focus:ring-[var(--sapling-orange)]"
                        />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ══ Step 1: Blocks ══ */}
            {wizardStep === 1 && (
              <FieldPicker
                farmId={farmId}
                farmName={farmName}
                blocks={blocks}
                setBlocks={setBlocks}
                crops={crops}
                analyses={availableAnalyses}
                otherFarms={clientFarms}
              />
            )}

            {/* ══ Step 2: Schedule Review ══ */}
            {wizardStep === 2 && (
              <>
                {scheduleError && (
                  <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                    {scheduleError}
                  </div>
                )}
                {unplanableBlocks.length > 0 && (
                  <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
                    <div className="flex items-start gap-2 text-amber-800">
                      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                      <div className="flex-1">
                        <p className="font-medium">
                          {unplanableBlocks.length} block{unplanableBlocks.length !== 1 ? "s" : ""} skipped
                        </p>
                        <ul className="mt-1 space-y-0.5 text-amber-700">
                          {unplanableBlocks.map((b) => (
                            <li key={b.block_id}>
                              <span className="font-medium">{b.block_name}</span>
                              {b.reason === "missing_targets" && " — no soil analysis linked"}
                              {b.reason === "missing_growth_stages" && ` — growth stages not configured for ${b.crop}`}
                            </li>
                          ))}
                        </ul>
                        <p className="mt-1 text-xs text-amber-600">
                          These blocks will be included in the programme once the missing data is supplied.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                {blockInfoData.length > 0 ? (
                  <ScheduleReview
                    blockInfo={blockInfoData}
                    onApplicationsChange={setUserApplications}
                    onPlantingMonthsChange={setPlantingMonths}
                    initialApplications={userApplications}
                    initialPlantingMonths={plantingMonths}
                  />
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
                  </div>
                )}
              </>
            )}

            {/* ══ Step 3: Blend Groups ══ */}
            {wizardStep === 3 && (
              <BlendGroups blendGroups={blendGroupsData} isAdmin={isAdmin} />
            )}

            {/* ══ Step 4: Review ══ */}
            {wizardStep === 4 && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Programme</p>
                    <p className="text-sm font-medium">{programmeName}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Season</p>
                    <p className="text-sm font-medium">{season || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Client</p>
                    <p className="text-sm font-medium">{clientName || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Farm</p>
                    <p className="text-sm font-medium">{farmName || "—"}</p>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-lg border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/30">
                        <th className="px-3 py-2 text-left font-medium">Block</th>
                        <th className="px-3 py-2 text-left font-medium">Crop</th>
                        <th className="px-3 py-2 text-left font-medium">Area</th>
                        <th className="px-3 py-2 text-left font-medium">Yield</th>
                      </tr>
                    </thead>
                    <tbody>
                      {blocks.filter((b) => b.crop && b.name).map((b, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="px-3 py-2 font-medium">{b.name}</td>
                          <td className="px-3 py-2">{b.crop} {b.cultivar && `(${b.cultivar})`}</td>
                          <td className="px-3 py-2">{b.area_ha ? `${b.area_ha} ha` : "—"}</td>
                          <td className="px-3 py-2">{b.yield_target ? `${b.yield_target} ${b.yield_unit}` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="rounded-lg bg-green-50 p-4 text-center">
                  <Check className="mx-auto size-8 text-green-600" />
                  <p className="mt-2 font-medium text-green-800">
                    {blendGroupsData.length} optimized blend{blendGroupsData.length !== 1 ? "s" : ""} ready
                  </p>
                  <p className="mt-1 text-sm text-green-700">
                    {userApplications.length} applications across {blocks.filter((b) => b.crop).length} blocks
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="mt-6 flex justify-between">
          <Button variant="outline" onClick={handleBack}>
            <ChevronLeft className="size-4" />
            {wizardStep === 0 ? "Cancel" : "Back"}
          </Button>

          {wizardStep < 4 ? (
            <Button
              onClick={handleNext}
              disabled={!canNext() || saving || generating}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {(saving || generating) ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <ChevronRight className="size-4" />
              )}
              {wizardStep === 1 ? "Preview Schedule" : wizardStep === 2 ? "Generate Blends" : "Next"}
            </Button>
          ) : (
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => handleFinish(false)}>
                Save as Draft
              </Button>
              <Button
                onClick={() => handleFinish(true)}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                <Check className="size-4" />
                Activate Programme
              </Button>
              <Button
                variant="outline"
                onClick={handleBuildArtifact}
                disabled={buildingArtifact}
                className="border-[var(--sapling-orange)] text-[var(--sapling-orange)] hover:bg-orange-50"
              >
                {buildingArtifact ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Leaf className="size-4" />
                )}
                Generate Full Programme
              </Button>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
