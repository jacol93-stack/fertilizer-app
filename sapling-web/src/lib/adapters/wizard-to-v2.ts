/**
 * Adapter: legacy season-manager wizard state → BuildProgrammeRequest.
 *
 * The old UI is kept; this adapter lets "Build Artifact (new engine)"
 * run alongside the legacy generate flow. Pure + unit-testable —
 * the wizard is responsible for pre-fetching soil_values per analysis.
 */
import type {
  BuildProgrammeRequest,
  BlockRequest,
  MethodAvailability,
} from "@/lib/types/programme-artifact";

export interface WizardBlock {
  name: string;
  area_ha: number | null;
  crop: string;
  cultivar: string;
  yield_target: number | null;
  yield_unit: string;
  soil_analysis_id: string | null;
  /** Perennial-only density. Drives backend per-ha scaling. */
  pop_per_ha?: number | null;
  /** Perennial-only years since planting. Drives age-factor scaling. */
  tree_age?: number | null;
}

export interface SoilAnalysisMeta {
  id: string;
  lab_name?: string | null;
  analysis_date?: string | null;
}

export interface WizardToV2Input {
  clientName: string;
  farmName: string;
  preparedFor?: string;
  season: string;
  clientId: string | null;
  blocks: WizardBlock[];
  /** Earliest wizard-assigned planting month per block, keyed by block.name. 1-12. */
  plantingMonthByBlockName: Record<string, number>;
  /** Full soil_values dict from soil_analyses.soil_values per analysis id. */
  soilValuesByAnalysisId: Record<string, Record<string, number>>;
  /** Soil analysis metadata (lab + sample date) per analysis id. */
  soilMetaByAnalysisId?: Record<string, SoilAnalysisMeta>;
  methodAvailability: MethodAvailability;
  /** NPK-ratio L1 distance threshold for clustering blocks. Lower =
   * more separate recipes; higher = simpler stock list for the farmer.
   * Default 0.25 — wizard surfaces it on the Schedule step. */
  clusterMargin?: number;
  /** block_id → cluster_id assignment overrides from the drag-drop
   * ClusterBoard. Empty → pure auto-clustering. */
  clusterAssignments?: Record<string, string>;
}

export class WizardAdapterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WizardAdapterError";
  }
}

const MONTHS: Record<number, string> = {
  1: "01", 2: "02", 3: "03", 4: "04", 5: "05", 6: "06",
  7: "07", 8: "08", 9: "09", 10: "10", 11: "11", 12: "12",
};

/**
 * Pick the season's start year. Accepts "2026/2027", "2026-2027", "2026", etc.
 * Falls back to current year if unparseable.
 */
function parseSeasonYear(season: string): number {
  const match = season.match(/\b(\d{4})\b/);
  if (match) return parseInt(match[1], 10);
  return new Date().getFullYear();
}

function monthToDate(year: number, month: number): string {
  const m = MONTHS[month] ?? "01";
  return `${year}-${m}-01`;
}

export interface SkippedBlock {
  block_name: string;
  reason: string;
  block_id?: string | null;
  block_area_ha?: number | null;
  attach_to_cluster?: string | null;
}

export interface WizardToV2Result {
  request: BuildProgrammeRequest;
  /**
   * Blocks the adapter could not include in the build (no soil analysis).
   * Carried alongside the request so the caller can surface them — the
   * backend attaches them to the artifact as OutstandingItem[] so they
   * appear in the final programme instead of being silently dropped.
   */
  skippedBlocks: SkippedBlock[];
}

/**
 * Map the wizard's collected state to a v2 BuildProgrammeRequest.
 *
 * Single-crop programmes only: if blocks span multiple crops, throws —
 * v2 expects one crop per build call. Multi-crop programmes should be
 * built as separate artifacts (one per crop group).
 *
 * Blocks without a linked soil analysis are surfaced via `skippedBlocks`
 * in the result (not silently dropped). Hard-invariant failures
 * (missing area_ha, yield_target, planting month, soil_values) still
 * throw — those are upstream bugs, not "come back later" situations.
 */
export function wizardStateToBuildRequest(
  input: WizardToV2Input,
): WizardToV2Result {
  const {
    clientName,
    farmName,
    preparedFor,
    season,
    clientId,
    blocks,
    plantingMonthByBlockName,
    soilValuesByAnalysisId,
    soilMetaByAnalysisId,
    methodAvailability,
  } = input;

  const namedBlocks = blocks.filter((b) => b.name && b.crop);
  const skippedBlocks: SkippedBlock[] = [];
  const usableBlocks: WizardBlock[] = [];
  const assignments = input.clusterAssignments ?? {};
  for (const b of namedBlocks) {
    // block_id convention in the wizard is the block name (matches what
    // the preview-schedule + cluster_assignments map keys on).
    const attach = assignments[b.name] ?? null;
    if (!b.soil_analysis_id) {
      skippedBlocks.push({
        block_name: b.name,
        reason: "no soil analysis linked",
        block_id: b.name,
        block_area_ha: b.area_ha,
        attach_to_cluster: attach,
      });
      continue;
    }
    const sv = soilValuesByAnalysisId[b.soil_analysis_id];
    if (!sv || Object.keys(sv).length === 0) {
      // Linked analysis exists but has no usable soil_values (e.g.
      // legacy row pre-dating soil_values column, or an incomplete
      // lab upload). Surface as skipped — same UX as "no analysis"
      // so the agronomist sees the gap on the artifact.
      skippedBlocks.push({
        block_name: b.name,
        reason: "linked soil analysis has no soil_values",
        block_id: b.name,
        block_area_ha: b.area_ha,
        attach_to_cluster: attach,
      });
      continue;
    }
    usableBlocks.push(b);
  }
  if (usableBlocks.length === 0) {
    throw new WizardAdapterError(
      "No blocks with usable soil values. Link or upload a complete soil analysis before building.",
    );
  }

  // v2 is single-crop per build. Reject mixed-crop programmes loudly
  // rather than silently picking one — that's the kind of thing that
  // causes quiet data corruption.
  const crops = new Set(usableBlocks.map((b) => b.crop));
  if (crops.size > 1) {
    throw new WizardAdapterError(
      `Mixed crops not supported in a single build (${Array.from(crops).join(", ")}). ` +
      `Build one artifact per crop.`,
    );
  }
  const crop = usableBlocks[0].crop;

  const year = parseSeasonYear(season);
  const plantingMonths = usableBlocks
    .map((b) => plantingMonthByBlockName[b.name])
    .filter((m): m is number => typeof m === "number" && m >= 1 && m <= 12);
  if (plantingMonths.length === 0) {
    throw new WizardAdapterError(
      "No planting month set for any block. Complete the Schedule step first.",
    );
  }
  const plantingMonth = Math.min(...plantingMonths);
  const plantingDate = monthToDate(year, plantingMonth);

  const blockRequests: BlockRequest[] = usableBlocks.map((b) => {
    // Earlier usableBlocks filter guarantees soil_analysis_id and
    // non-empty soil_values; remaining checks are on block-level
    // fields the wizard should have captured upstream.
    const soilValues = soilValuesByAnalysisId[b.soil_analysis_id!];
    if (!b.area_ha || b.area_ha <= 0) {
      throw new WizardAdapterError(
        `Block "${b.name}" has no area_ha — required for v2 build.`,
      );
    }
    if (!b.yield_target || b.yield_target <= 0) {
      throw new WizardAdapterError(
        `Block "${b.name}" has no yield_target — required for v2 build.`,
      );
    }
    const meta = soilMetaByAnalysisId?.[b.soil_analysis_id!];
    return {
      block_id: b.name,
      block_name: b.name,
      block_area_ha: b.area_ha,
      soil_parameters: soilValues,
      yield_target_per_ha: b.yield_target,
      lab_name: meta?.lab_name ?? null,
      sample_date: meta?.analysis_date ?? null,
      pre_season_inputs: [],
      pop_per_ha: b.pop_per_ha ?? null,
      tree_age: b.tree_age ?? null,
    };
  });

  const request: BuildProgrammeRequest = {
    client_name: clientName || "Unknown client",
    farm_name: farmName || "Unknown farm",
    prepared_for: preparedFor || clientName || "Unknown recipient",
    crop,
    planting_date: plantingDate,
    season,
    client_id: clientId,
    blocks: blockRequests,
    method_availability: methodAvailability,
    skipped_blocks: skippedBlocks,
    ...(input.clusterMargin !== undefined && { cluster_margin: input.clusterMargin }),
    ...(Object.keys(assignments).length > 0 && { cluster_assignments: assignments }),
  };
  return { request, skippedBlocks };
}

/**
 * Default method availability — used as a fallback when no field data
 * is available (e.g. a manual-entry flow that skips the field picker).
 */
export function defaultMethodAvailability(): MethodAvailability {
  return {
    has_drip: false,
    has_pivot: false,
    has_sprinkler: false,
    has_foliar_sprayer: true,
    has_granular_spreader: true,
    has_fertigation_injectors: false,
    has_seed_treatment: false,
  };
}

/**
 * Aggregate the set of field-level accepted_methods strings into the
 * farm-level MethodAvailability shape the engine expects.
 *
 * The field drawer captures per-field strings like "broadcast" /
 * "fertigation" / "foliar" / "band_place" — the union across the
 * programme's selected blocks tells the orchestrator which methods
 * it may route nutrients through.
 *
 * We default all irrigation variants (drip / pivot / sprinkler) from
 * a single "fertigation" marker because the field data doesn't
 * currently split that out per-block; downstream the method_selector
 * treats them uniformly. If a field explicitly names "drip" /
 * "pivot" / "sprinkler", those take priority.
 */
export function deriveMethodAvailability(
  acceptedMethods: string[],
): MethodAvailability {
  const set = new Set(acceptedMethods.map((m) => m.toLowerCase().trim()));
  const hasAny = (...keys: string[]) => keys.some((k) => set.has(k));

  const fertigation = hasAny("fertigation", "drip", "pivot", "sprinkler");
  return {
    has_drip: hasAny("drip") || (fertigation && !hasAny("pivot", "sprinkler")),
    has_pivot: hasAny("pivot"),
    has_sprinkler: hasAny("sprinkler", "micro"),
    has_foliar_sprayer: hasAny("foliar", "foliar_spray"),
    has_granular_spreader: hasAny(
      "broadcast", "band_place", "banded", "side_dress", "topdress",
    ),
    has_fertigation_injectors: fertigation,
    has_seed_treatment: hasAny("seed_treat", "seed_treatment"),
  };
}
