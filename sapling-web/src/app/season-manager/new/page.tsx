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
import type { Block, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { emptyBlock, MONTH_NAMES, methodLabel } from "@/lib/season-constants";
import {
  wizardStateToBuildRequest,
  deriveMethodAvailability,
  WizardAdapterError,
  type SoilAnalysisMeta,
} from "@/lib/adapters/wizard-to-v2";
import { buildProgramme, previewSchedule, type ClusterPreview } from "@/lib/programmes-v2";
import { ClusterBoard, type DatalessBlock } from "@/components/season-manager/cluster-board";
import { assignmentsFromClusters, type BlockTargets } from "@/lib/cluster-heterogeneity";
import type { Blend as ArtifactBlend, ProgrammeArtifact } from "@/lib/types/programme-artifact";

export default function SeasonBuilderPageWrapper() {
  return (
    <Suspense>
      <SeasonBuilderPage />
    </Suspense>
  );
}

const STEPS = ["Client", "Blocks", "Schedule", "Blends", "Review"];

const FOLIAR_METHODS = new Set(["foliar", "foliar_spray"]);

const NUMERIC_RATE_RE = /([\d.]+)/;

function parseRatePerHa(s: string | null | undefined): number {
  if (!s) return 0;
  const m = NUMERIC_RATE_RE.exec(s);
  return m ? parseFloat(m[1]) : 0;
}

function methodKindForBlendGroups(method: string): string {
  // ApplicationMethod enum values map onto the legacy BlendGroups display
  // labels (broadcast / fertigation / foliar). Drop method-specific
  // qualifiers so the UI stays compact.
  const m = method.toLowerCase();
  if (m.includes("foliar")) return "foliar";
  if (m.includes("fertig")) return "fertigation";
  if (m.includes("seed")) return "seed_treat";
  if (m.includes("basal")) return "soil_basal";
  return "broadcast";
}

function eventDateToMonth(iso: string | undefined): number {
  if (!iso) return 1;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return 1;
  return d.getMonth() + 1;
}

/** Map a v2 ProgrammeArtifact's blends list into the BlendGroupData
 * shape the existing BlendGroups component expects. One group per
 * block; each blend's ApplicationEvents become one ApplicationBlendData
 * row each so the wizard preview shows real per-event timing. */
function artifactToBlendGroups(
  artifact: ProgrammeArtifact,
  wizardBlocks: Omit<Block, "id">[],
): BlendGroupData[] {
  const blends = (artifact.blends || []) as ArtifactBlend[];
  const snapshots = artifact.soil_snapshots || [];
  const cropByBlockId = new Map<string, string>();
  for (const wb of wizardBlocks) {
    if (wb.crop && wb.name) cropByBlockId.set(wb.name, wb.crop);
  }
  const areaByBlockId = new Map<string, number>();
  for (const s of snapshots) {
    if (s.block_id && typeof s.block_area_ha === "number") {
      areaByBlockId.set(s.block_id, s.block_area_ha);
    }
  }

  const groupMap = new Map<string, BlendGroupData>();
  for (const blend of blends) {
    const blockId = blend.block_id;
    if (!groupMap.has(blockId)) {
      const crop = cropByBlockId.get(blockId) || "";
      groupMap.set(blockId, {
        group: blockId,
        crops: crop ? [crop] : [],
        block_names: [blockId],
        total_area_ha: areaByBlockId.get(blockId) ?? 0,
        applications: [],
      });
    }
    const group = groupMap.get(blockId)!;
    const method = methodKindForBlendGroups(String(blend.method));
    const isFoliar = FOLIAR_METHODS.has(method);
    const recipe = (blend.raw_products || []).map((p) => ({
      material: p.product,
      type: p.analysis,
      kg: parseRatePerHa(p.rate_per_event_per_ha),
      pct: 0,
      cost: 0,
    }));
    const ratePerEvent = recipe.reduce((s, r) => s + (r.kg || 0), 0);
    const events = blend.applications && blend.applications.length > 0
      ? blend.applications
      : [{ event_index: 0, event_date: "", week_from_planting: 0 }];
    for (const ev of events) {
      group.applications.push({
        stage_name: blend.stage_name,
        month: eventDateToMonth(ev.event_date),
        method,
        sa_notation: blend.raw_products?.map((p) => p.analysis).filter(Boolean).join(" + ") || "",
        rate_kg_ha: ratePerEvent,
        recipe,
        is_foliar: isFoliar,
      });
    }
  }
  return Array.from(groupMap.values());
}

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

  // v2 ProgrammeArtifact id, set when buildProgramme() succeeds at step 2→3.
  const [artifactId, setArtifactId] = useState<string | null>(null);

  // Schedule data (from v2 preview-schedule)
  const [blockInfoData, setBlockInfoData] = useState<BlockInfo[]>([]);
  const [userApplications, setUserApplications] = useState<UserApplication[]>([]);
  const [plantingMonths, setPlantingMonths] = useState<Record<string, number>>({});
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [unplanableBlocks, setUnplanableBlocks] = useState<Array<{ block_id: string; block_name: string; reason: string; crop?: string }>>([]);

  // Blend groups display data — mapped from the v2 ProgrammeArtifact's
  // blends after step 2→3 build. One group per cluster.
  const [blendGroupsData, setBlendGroupsData] = useState<BlendGroupData[]>([]);

  // Cluster preview from /preview-schedule. Drives the "blocks share
  // recipe X / Y" summary on the Schedule step. Lower margin → more
  // recipes the farmer mixes; higher margin → simpler stock list.
  const [clusters, setClusters] = useState<ClusterPreview[]>([]);
  const [clusterMargin, setClusterMargin] = useState<number>(0.25);
  // Per-block v2 targets surfaced by preview-schedule. Used by the
  // ClusterBoard to recompute heterogeneity client-side on drag-drop.
  const [blockTargets, setBlockTargets] = useState<BlockTargets[]>([]);
  // block_id → cluster_id. Persisted in the wizard draft + sent to the
  // preview-schedule + build endpoints so user reassignments survive.
  const [clusterAssignments, setClusterAssignments] = useState<Record<string, string>>({});

  // Method availability is derived from field-level accepted_methods +
  // irrigation_type during the build — not a separate wizard step.
  // Field drawer is the single source of truth.
  const [buildingArtifact, setBuildingArtifact] = useState(false);

  // Reference data
  const [crops, setCrops] = useState<CropNorm[]>([]);
  const [availableAnalyses, setAvailableAnalyses] = useState<SoilAnalysis[]>([]);
  const [clientFarms, setClientFarms] = useState<Array<{ id: string; name: string }>>([]);

  // ── Wizard draft persistence ────────────────────────────────────
  // Survive accidental refreshes mid-wizard. Persist to localStorage
  // on any state change; rehydrate on mount unless the URL is
  // carrying a fresh handoff (analysis_id / client_id), in which
  // case the handoff intent wins. Cleared on Build Full Programme
  // and explicit Cancel.
  // v2 = post-legacy-rip key — drops `programmeId`, adds `artifactId`.
  const DRAFT_KEY = "sapling.wizard.draft.v2";
  const hasHydrated = useRef(false);

  useEffect(() => {
    // Run once. Skip hydration when the URL is handing off a fresh
    // intent — a stale draft would silently override the link the
    // user just clicked.
    if (hasHydrated.current) return;
    hasHydrated.current = true;
    if (analysisId || urlClientId) return;
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw) as {
        wizardStep?: number;
        clientId?: string;
        farmId?: string;
        clientName?: string;
        farmName?: string;
        programmeName?: string;
        season?: string;
        blocks?: Omit<Block, "id">[];
        artifactId?: string | null;
        blockInfoData?: BlockInfo[];
        userApplications?: UserApplication[];
        plantingMonths?: Record<string, number>;
        blendGroupsData?: BlendGroupData[];
        clusterMargin?: number;
        clusterAssignments?: Record<string, string>;
      };
      if (typeof draft.wizardStep === "number") setWizardStep(draft.wizardStep);
      if (draft.clientId) setClientId(draft.clientId);
      if (draft.farmId) setFarmId(draft.farmId);
      if (draft.clientName) setClientName(draft.clientName);
      if (draft.farmName) setFarmName(draft.farmName);
      if (draft.programmeName) setProgrammeName(draft.programmeName);
      if (draft.season) setSeason(draft.season);
      if (draft.blocks) setBlocks(draft.blocks);
      if (draft.artifactId !== undefined) setArtifactId(draft.artifactId);
      if (draft.blockInfoData) setBlockInfoData(draft.blockInfoData);
      if (draft.userApplications) setUserApplications(draft.userApplications);
      if (draft.plantingMonths) setPlantingMonths(draft.plantingMonths);
      if (draft.blendGroupsData) setBlendGroupsData(draft.blendGroupsData);
      if (typeof draft.clusterMargin === "number") setClusterMargin(draft.clusterMargin);
      if (draft.clusterAssignments) setClusterAssignments(draft.clusterAssignments);
      toast.message("Resumed where you left off");
    } catch {
      // Bad JSON or shape mismatch — clear the slot rather than
      // crash the page on every load.
      try { window.localStorage.removeItem(DRAFT_KEY); } catch {}
    }
  }, [analysisId, urlClientId]);

  useEffect(() => {
    if (!hasHydrated.current) return;
    if (typeof window === "undefined") return;
    // Only persist once the user has named a programme — empty
    // drafts add noise without value.
    if (!programmeName && wizardStep === 0) return;
    try {
      const draft = {
        wizardStep, clientId, farmId, clientName, farmName,
        programmeName, season, blocks, artifactId,
        blockInfoData, userApplications, plantingMonths, blendGroupsData,
        clusterMargin, clusterAssignments,
      };
      window.localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    } catch {
      // Quota or storage-disabled — fail silently; user keeps
      // their in-memory wizard state.
    }
  }, [wizardStep, clientId, farmId, clientName, farmName, programmeName,
      season, blocks, artifactId, blockInfoData, userApplications,
      plantingMonths, blendGroupsData, clusterMargin, clusterAssignments]);

  const clearDraft = () => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(DRAFT_KEY);
      }
    } catch {}
  };

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
    // Only auto-fill once a client (and ideally farm) is actually
    // selected — clientName fires on every keystroke in the search
    // box, so gating on clientId avoids capturing a partial query
    // like "Vrystaa" as the programme name.
    if (clientId && clientName && !programmeName) {
      setProgrammeName(farmName ? `${clientName} — ${farmName}` : clientName);
    }
    if (!season) {
      const year = new Date().getFullYear();
      setSeason(`${year}/${year + 1}`);
    }
  }, [clientId, clientName, farmName]);

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

  // Step 1→2: Resolve growth stages, accepted methods, nutrient targets
  // and corrections per block via the v2 preview-schedule endpoint.
  // Stateless — no DB writes.
  const handleAdvanceToSchedule = async () => {
    if (!clientId) {
      toast.error("Please select a client");
      return;
    }

    setSaving(true);
    setScheduleError(null);
    try {
      const validBlocks = blocks.filter((b) => b.crop && b.name);
      if (validBlocks.length === 0) {
        throw new Error("Add at least one block with a crop on Step 1.");
      }
      const previewBlocks = validBlocks.map((b) => ({
        block_id: b.name,
        block_name: b.name,
        crop: b.crop!,
        cultivar: b.cultivar || null,
        soil_analysis_id: b.soil_analysis_id || null,
        field_id: (b as { field_id?: string | null }).field_id ?? null,
        area_ha: b.area_ha ?? null,
        yield_target: b.yield_target ?? null,
        yield_unit: b.yield_unit || null,
        tree_age: b.tree_age ?? null,
        pop_per_ha: b.pop_per_ha ?? null,
      }));
      const preview = await previewSchedule(previewBlocks, {
        clusterMargin,
        clusterAssignments,
      });
      setBlockInfoData(preview.block_info as unknown as BlockInfo[]);
      setUnplanableBlocks(preview.unplanable_blocks || []);
      setClusters(preview.clusters || []);

      // Pull per-block targets out of the block_info payload for the
      // ClusterBoard's local-recompute helper.
      const targets: BlockTargets[] = [];
      for (const bi of preview.block_info as unknown as Array<Record<string, unknown>>) {
        const t = bi.v2_season_targets as Record<string, number> | undefined;
        if (!t) continue;
        targets.push({
          block_id: String(bi.block_id),
          block_name: String(bi.block_name),
          block_area_ha: Number(bi.block_area_ha) || 1,
          targets: t,
        });
      }
      setBlockTargets(targets);

      // Seed the assignment map from the server's auto-clustering on the
      // first preview, but preserve user overrides on re-fetch.
      setClusterAssignments((prev) => {
        const seed = assignmentsFromClusters(preview.clusters || []);
        // Preserve any user assignments whose block_id is still in seed.
        for (const [bid, cid] of Object.entries(prev)) {
          if (seed[bid] !== undefined) seed[bid] = cid;
        }
        return seed;
      });
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

  // Step 2→3: Run the v2 builder, persist the artifact (state=draft),
  // and map artifact.blends → BlendGroupData for the preview step.
  const handleAdvanceToBlends = async () => {
    setGenerating(true);
    try {
      const validBlocks = blocks.filter((b) => b.crop && b.name && b.soil_analysis_id);
      if (validBlocks.length === 0) {
        throw new Error("No blocks have a soil analysis linked. Go back to Step 1 and link one.");
      }
      if (blockInfoData.length === 0) {
        throw new Error("Schedule isn't ready. Go back to Step 2 first.");
      }

      // Resolve planting month per block — user-set on Step 2, fallback
      // to first growth-stage month if the user accepted defaults.
      const plantingMonthByBlockName: Record<string, number> = {};
      for (const bi of blockInfoData) {
        const userSet = plantingMonths[bi.block_id];
        const fallback = bi.growth_stages?.[0]?.month_start;
        const month = userSet ?? fallback;
        if (typeof month === "number" && month >= 1 && month <= 12) {
          plantingMonthByBlockName[bi.block_name] = month;
        }
      }
      if (Object.keys(plantingMonthByBlockName).length === 0) {
        throw new Error("No planting months available. Set one on Step 2 (Schedule) for each block.");
      }

      // Fetch soil_values per analysis (list endpoint omits them).
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

      const allAcceptedMethods = blockInfoData.flatMap((bi) => bi.accepted_methods || []);
      const methodAvailability = deriveMethodAvailability(allAcceptedMethods);

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
          pop_per_ha: b.pop_per_ha,
          tree_age: b.tree_age,
        })),
        plantingMonthByBlockName,
        soilValuesByAnalysisId,
        soilMetaByAnalysisId,
        methodAvailability,
        clusterMargin,
        clusterAssignments,
      });

      const response = await buildProgramme(request);
      setArtifactId(response.id);
      setBlendGroupsData(artifactToBlendGroups(response.artifact as ProgrammeArtifact, blocks));

      if (skippedBlocks.length > 0) {
        toast.warning(
          `${skippedBlocks.length} block${skippedBlocks.length !== 1 ? "s" : ""} not planned (no soil analysis) — see Outstanding Items`,
        );
      }
      setWizardStep(3);
    } catch (e) {
      console.error("handleAdvanceToBlends failed", e);
      if (e instanceof WizardAdapterError) {
        toast.error(e.message, { duration: 10000 });
      } else if (e instanceof Error) {
        toast.error(e.message, { duration: 10000 });
      } else {
        toast.error("Generation failed (unknown error — check console)", { duration: 10000 });
      }
    } finally {
      setGenerating(false);
    }
  };

  // Step 4 (Review) → navigate to the persisted artifact view. The
  // artifact was saved as draft when the user advanced past Step 2.
  const handleBuildArtifact = () => {
    if (!artifactId) {
      toast.error("Programme not built yet — go back to Step 3 first.");
      return;
    }
    setBuildingArtifact(true);
    clearDraft();
    router.push(`/season-manager/artifact/${artifactId}`);
  };

  // ── Validation ──────────────────────────────────────────────────
  const canNext = () => {
    // Step 0: client + farm + programme name all required. Helper text
    // says "A programme covers a whole farm" — enforce that here so
    // step 1's FieldPicker doesn't render its empty/confusing state.
    if (wizardStep === 0) return !!programmeName && !!clientId && !!farmId;
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
      // Cancel from step 0 = abandon the draft. Clear the saved
      // copy so the next visit starts clean.
      clearDraft();
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
              className={`flex-1 truncate whitespace-nowrap rounded-md px-2 py-2 text-xs font-medium transition-colors sm:px-3 sm:text-sm ${
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
                {(blockTargets.length > 0 || unplanableBlocks.length > 0) && (
                  <ClusterBoard
                    blocks={blockTargets}
                    datalessBlocks={unplanableBlocks
                      .filter((u) => u.reason === "missing_targets")
                      .map((u): DatalessBlock => {
                        const wb = blocks.find((b) => b.name === u.block_id);
                        return {
                          block_id: u.block_id,
                          block_name: u.block_name,
                          block_area_ha: wb?.area_ha ?? null,
                        };
                      })}
                    assignments={clusterAssignments}
                    onAssignmentsChange={setClusterAssignments}
                    margin={clusterMargin}
                    onMarginChange={async (m) => {
                      setClusterMargin(m);
                      await handleAdvanceToSchedule();
                    }}
                    busy={saving}
                    knownClusterIds={clusters.map((c) => c.cluster_id)}
                  />
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

                {/* Per-block summary with season nutrient targets.
                    Programme builder is agronomy-scoped (see
                    project_programme_builder_scope memory) — surface
                    nutrient kg/ha, never cost. The legacy preview
                    endpoint emits element-form keys (N / P / K) so we
                    match that here; oxide-form (P₂O₅ / K₂O) belongs
                    to the rendered ProgrammeArtifact / PDF. */}
                <div className="overflow-x-auto rounded-lg border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/30">
                        <th className="px-3 py-2 text-left font-medium">Block</th>
                        <th className="px-3 py-2 text-left font-medium">Crop</th>
                        <th className="px-3 py-2 text-left font-medium">Area</th>
                        <th className="px-3 py-2 text-left font-medium">Yield</th>
                        <th className="px-3 py-2 text-right font-medium">N kg/ha</th>
                        <th className="px-3 py-2 text-right font-medium">P kg/ha</th>
                        <th className="px-3 py-2 text-right font-medium">K kg/ha</th>
                      </tr>
                    </thead>
                    <tbody>
                      {blocks.filter((b) => b.crop && b.name).map((b, i) => {
                        const bi = blockInfoData.find((x) => x.block_name === b.name);
                        const target = (nutrient: string) => {
                          const t = bi?.nutrient_targets?.find((nt) => {
                            const n = (nt.Nutrient || nt.nutrient || "").toLowerCase();
                            return n === nutrient.toLowerCase();
                          });
                          const v = t?.Target_kg_ha ?? t?.target_kg_ha;
                          return typeof v === "number" ? v.toFixed(0) : "—";
                        };
                        return (
                          <tr key={i} className="border-b last:border-0">
                            <td className="px-3 py-2 font-medium">{b.name}</td>
                            <td className="px-3 py-2">{b.crop} {b.cultivar && `(${b.cultivar})`}</td>
                            <td className="px-3 py-2">{b.area_ha ? `${b.area_ha} ha` : "—"}</td>
                            <td className="px-3 py-2">{b.yield_target ? `${b.yield_target} ${b.yield_unit}` : "—"}</td>
                            <td className="px-3 py-2 text-right tabular-nums">{target("N")}</td>
                            <td className="px-3 py-2 text-right tabular-nums">{target("P")}</td>
                            <td className="px-3 py-2 text-right tabular-nums">{target("K")}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Application schedule preview — agronomist owns timing
                    (see project_application_timing_and_blend_count memory),
                    so surface the chosen month + method per block right
                    on the Review screen so they can spot misses before
                    sign-off. */}
                {userApplications.length > 0 && (
                  <div className="rounded-lg border">
                    <p className="border-b px-3 py-2 text-xs font-medium uppercase text-muted-foreground">
                      Application Schedule
                    </p>
                    <div className="divide-y">
                      {(() => {
                        // Group by month, then by method, listing the
                        // blocks affected. Keeps the preview compact
                        // even on shared-schedule programmes.
                        type Entry = { month: number; method: string; blockIds: Set<string> };
                        const byKey: Record<string, Entry> = {};
                        for (const a of userApplications) {
                          const key = `${a.month}|${a.method}`;
                          if (!byKey[key]) {
                            byKey[key] = { month: a.month, method: a.method, blockIds: new Set() };
                          }
                          byKey[key].blockIds.add(a.block_id);
                        }
                        const blockNameById = new Map(
                          blockInfoData.map((bi) => [bi.block_id, bi.block_name]),
                        );
                        const totalBlocks = blockInfoData.length;
                        const rows = Object.values(byKey).sort(
                          (x, y) => x.month - y.month || x.method.localeCompare(y.method),
                        );
                        return rows.map((r, i) => {
                          const all = r.blockIds.size === totalBlocks && totalBlocks > 0;
                          const names = all
                            ? "all blocks"
                            : Array.from(r.blockIds)
                                .map((id) => blockNameById.get(id) || id)
                                .sort()
                                .join(", ");
                          return (
                            <div key={i} className="flex items-center justify-between px-3 py-2 text-sm">
                              <div className="flex items-center gap-3">
                                <span className="inline-flex w-9 justify-center rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                                  {MONTH_NAMES[r.month]}
                                </span>
                                <span className="font-medium text-[var(--sapling-dark)]">
                                  {methodLabel(r.method)}
                                </span>
                              </div>
                              <span className="text-xs text-muted-foreground">{names}</span>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  </div>
                )}

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
            {wizardStep === 0 ? "Cancel & return to Season Manager" : "Back"}
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
            // The v2 build runs at Step 2→3, persisting an artifact in
            // draft state. This button just navigates to the saved
            // artifact view.
            <Button
              onClick={handleBuildArtifact}
              disabled={buildingArtifact || !artifactId}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {buildingArtifact ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Leaf className="size-4" />
              )}
              View Full Programme
            </Button>
          )}
        </div>
      </div>
    </AppShell>
  );
}
