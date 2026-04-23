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

/**
 * Map the wizard's collected state to a v2 BuildProgrammeRequest.
 *
 * Single-crop programmes only: if blocks span multiple crops, throws —
 * v2 expects one crop per build call. Multi-crop programmes should be
 * built as separate artifacts (one per crop group).
 */
export function wizardStateToBuildRequest(
  input: WizardToV2Input,
): BuildProgrammeRequest {
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

  const usableBlocks = blocks.filter(
    (b) => b.name && b.crop && b.soil_analysis_id,
  );
  if (usableBlocks.length === 0) {
    throw new WizardAdapterError(
      "No blocks with a linked soil analysis. Add one before building.",
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
    const soilValues = soilValuesByAnalysisId[b.soil_analysis_id!];
    if (!soilValues) {
      throw new WizardAdapterError(
        `Missing soil_values for block "${b.name}" ` +
        `(analysis ${b.soil_analysis_id}). Fetch before adapting.`,
      );
    }
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
    };
  });

  return {
    client_name: clientName || "Unknown client",
    farm_name: farmName || "Unknown farm",
    prepared_for: preparedFor || clientName || "Unknown recipient",
    crop,
    planting_date: plantingDate,
    season,
    client_id: clientId,
    blocks: blockRequests,
    method_availability: methodAvailability,
  };
}

/**
 * Default method availability — matches Pydantic defaults in the backend
 * model. Render as 7 checkboxes in the wizard; this is the initial state.
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
