/**
 * Block data-completeness rulebook.
 *
 * Single source of truth for "is this block ready for programme
 * building?" Used by FieldPicker (inline checklist), the schedule
 * step's unplanable-blocks banner, and the artifact OutstandingItem
 * generator — so the set of fields we call "compulsory" never drifts
 * between surfaces.
 *
 * Each requirement knows: its human name, how to check it, whether
 * it's hard-required (absence = block excluded) or a soft warning
 * (absence = programme builds with assumptions).
 */
import type { Block } from "@/lib/season-constants";

/** Shape that both wizard blocks (Omit<Block,"id">) and server-hydrated
 * blocks (with id) satisfy. Uses the fields we actually check. */
export interface CheckableBlock {
  name: string;
  crop: string;
  area_ha: number | null;
  yield_target: number | null;
  yield_unit?: string;
  tree_age: number | null;
  pop_per_ha?: number | null;
  soil_analysis_id: string | null;
  /** Optional: the crop's type from crop_requirements. When known,
   * enables perennial-specific checks (tree_age, pop_per_ha). */
  crop_type?: "annual" | "perennial" | string | null;
}

export type Severity = "hard" | "soft";

export interface CompletenessIssue {
  /** Stable machine key for UI wiring (e.g. to focus the right input). */
  key:
    | "crop"
    | "area_ha"
    | "yield_target"
    | "soil_analysis"
    | "tree_age"
    | "pop_per_ha";
  /** Human-readable label for the checklist. */
  label: string;
  severity: Severity;
  /** One-line why-it-matters, shown on hover / expanded row. */
  hint: string;
}

export interface CompletenessReport {
  /** No hard issues — block is eligible for the build. Soft issues
   * may still be present and should be surfaced as assumptions. */
  complete: boolean;
  hardIssues: CompletenessIssue[];
  softIssues: CompletenessIssue[];
  /** All issues, hard first then soft, in stable render order. */
  issues: CompletenessIssue[];
}

const RULES: Array<(b: CheckableBlock) => CompletenessIssue | null> = [
  // ── Hard requirements ─────────────────────────────────────────
  (b) => !b.crop
    ? {
        key: "crop",
        label: "Crop",
        severity: "hard",
        hint: "Engine keys every calculation off the crop type. No crop = no programme.",
      }
    : null,

  (b) => !b.soil_analysis_id
    ? {
        key: "soil_analysis",
        label: "Soil analysis",
        severity: "hard",
        hint: "Soil values drive the nutrient targets. Without one, the block is skipped from planning and surfaced as an OutstandingItem on the artifact.",
      }
    : null,

  (b) => !b.area_ha || b.area_ha <= 0
    ? {
        key: "area_ha",
        label: "Area (ha)",
        severity: "hard",
        hint: "Area scales the per-ha targets into real kg totals. Zero area → zero output.",
      }
    : null,

  (b) => !b.yield_target || b.yield_target <= 0
    ? {
        key: "yield_target",
        label: "Yield target",
        severity: "hard",
        hint: "Nutrient targets scale with expected yield. Zero or missing = FERTASA table can't be read.",
      }
    : null,

  // ── Soft requirements (perennial-specific) ────────────────────
  (b) => {
    if (b.crop_type !== "perennial") return null;
    if (b.tree_age != null && b.tree_age > 0) return null;
    return {
      key: "tree_age",
      label: "Tree age",
      severity: "soft",
      hint: "Perennials use age-factors to scale young vs mature orchard rates. Missing defaults to mature.",
    };
  },

  (b) => {
    if (b.crop_type !== "perennial") return null;
    if (b.pop_per_ha != null && b.pop_per_ha > 0) return null;
    return {
      key: "pop_per_ha",
      label: "Trees / ha",
      severity: "soft",
      hint: "SAMAC / tree-crop rates scale with tree density. Missing defaults to the crop's reference density.",
    };
  },
];

export function blockCompleteness(block: CheckableBlock): CompletenessReport {
  const hit: CompletenessIssue[] = [];
  for (const rule of RULES) {
    const issue = rule(block);
    if (issue) hit.push(issue);
  }
  const hardIssues = hit.filter((i) => i.severity === "hard");
  const softIssues = hit.filter((i) => i.severity === "soft");
  return {
    complete: hardIssues.length === 0,
    hardIssues,
    softIssues,
    issues: [...hardIssues, ...softIssues],
  };
}

/** Convenience: summarise a list of blocks for a top-of-page banner. */
export function summariseCompleteness(
  blocks: CheckableBlock[],
): { total: number; ready: number; withHardGaps: number; withSoftGaps: number } {
  let ready = 0;
  let withHardGaps = 0;
  let withSoftGaps = 0;
  for (const b of blocks) {
    const r = blockCompleteness(b);
    if (r.complete) ready += 1;
    if (r.hardIssues.length > 0) withHardGaps += 1;
    if (r.softIssues.length > 0) withSoftGaps += 1;
  }
  return { total: blocks.length, ready, withHardGaps, withSoftGaps };
}

/** Map a block's wizard shape to the CheckableBlock shape. Accepts the
 * Block type directly; crop_type must be supplied by the caller if
 * known (it lives on CropNorm / crop_requirements, not on Block). */
export function toCheckable(
  block: Block | Omit<Block, "id">,
  cropType?: string | null,
): CheckableBlock {
  return {
    name: block.name,
    crop: block.crop,
    area_ha: block.area_ha,
    yield_target: block.yield_target,
    yield_unit: block.yield_unit,
    tree_age: block.tree_age,
    pop_per_ha: block.pop_per_ha,
    soil_analysis_id: block.soil_analysis_id,
    crop_type: cropType ?? null,
  };
}
