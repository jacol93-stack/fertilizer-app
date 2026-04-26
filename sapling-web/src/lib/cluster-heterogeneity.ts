/**
 * Client-side mirror of the backend's heterogeneity computation
 * (block_clustering.py — aggregate_cluster + classify_heterogeneity).
 *
 * Used during drag-and-drop in the wizard so each cluster's CV pills
 * update instantly without a network round-trip. The /api/programmes/v2/
 * preview-schedule + build endpoints remain the source of truth — this
 * is purely UI-side previewing.
 *
 * Math: per-nutrient mean, sample standard deviation, CV% = 100 * sd / mean.
 * Identical to the backend's aggregate_samples + classify_heterogeneity.
 */

import type { ClusterPreview, HeterogeneityWarning } from "./programmes-v2";

// Mirror of HETEROGENEITY_THRESHOLDS in block_clustering.py
const HETEROGENEITY_THRESHOLDS: Record<string, { warn: number; split: number }> = {
  P2O5: { warn: 35.0, split: 50.0 },
  K2O:  { warn: 25.0, split: 35.0 },
  N:    { warn: 30.0, split: 50.0 },
  Ca:   { warn: 30.0, split: 50.0 },
  Mg:   { warn: 30.0, split: 50.0 },
  S:    { warn: 30.0, split: 50.0 },
};
const FALLBACK_THRESHOLD = { warn: 30.0, split: 50.0 };

const HETEROGENEITY_CITATION = "Wilding (1985) via Mulla & Schepers (1997)";

export type HeterogeneityLevel = "ok" | "warn" | "split";

export function classifyLevel(nutrient: string, cvPct: number | null): HeterogeneityLevel {
  if (cvPct == null) return "ok";
  const t = HETEROGENEITY_THRESHOLDS[nutrient] ?? FALLBACK_THRESHOLD;
  if (cvPct >= t.split) return "split";
  if (cvPct >= t.warn) return "warn";
  return "ok";
}

/** Per-block view used by the recompute helper. block_id keys back into
 * cluster assignments; targets is the same dict the backend clusters on. */
export interface BlockTargets {
  block_id: string;
  block_name: string;
  block_area_ha: number;
  targets: Record<string, number>;
}

/** Recompute clusters from a fresh assignment map. Mirrors the backend's
 * cluster_and_aggregate output shape so the React state stays uniform
 * regardless of source (server preview vs local recompute). */
export function recomputeClusters(
  blocks: BlockTargets[],
  assignments: Record<string, string>,
): ClusterPreview[] {
  // Group by assigned cluster id. Blocks with no assignment go into
  // singleton clusters keyed by their own block_id (lower-cased) — the
  // user is mid-drag and hasn't placed them yet.
  const groupsById: Record<string, BlockTargets[]> = {};
  const orderedIds: string[] = [];
  for (const b of blocks) {
    const cid = assignments[b.block_id] ?? `_unassigned_${b.block_id}`;
    if (!groupsById[cid]) {
      groupsById[cid] = [];
      orderedIds.push(cid);
    }
    groupsById[cid].push(b);
  }

  // Build a ClusterPreview for each group.
  return orderedIds
    .filter((cid) => !cid.startsWith("_unassigned_"))
    .map((cid) => buildClusterPreview(cid, groupsById[cid]));
}

function buildClusterPreview(cid: string, blocks: BlockTargets[]): ClusterPreview {
  const nutrients = collectNutrientKeys(blocks);
  const useArea = blocks.every((b) => b.block_area_ha > 0);
  const totalArea = blocks.reduce((s, b) => s + (b.block_area_ha || 0), 0);

  const aggregated: Record<string, number> = {};
  const perNutrient: Record<string, { cv_pct: number | null; n: number; level: string }> = {};
  const warnings: HeterogeneityWarning[] = [];
  let anyWarn = false;
  let anySplit = false;

  for (const nut of nutrients) {
    const values: number[] = [];
    const weights: number[] = [];
    for (const b of blocks) {
      const v = b.targets[nut];
      if (typeof v !== "number") continue;
      values.push(v);
      weights.push(useArea ? (b.block_area_ha || 0) : 1);
    }
    if (values.length === 0) continue;

    const mean = weightedMean(values, weights);
    aggregated[nut] = round1(mean);

    // Sample CV% — same form as the backend (population would understate
    // small clusters). Skip CV when fewer than 2 samples.
    const cvPct = values.length >= 2 ? sampleCvPct(values, mean) : null;
    const level = classifyLevel(nut, cvPct);
    perNutrient[nut] = {
      cv_pct: cvPct == null ? null : round1(cvPct),
      n: values.length,
      level,
    };
    if (level === "warn" || level === "split") {
      const threshold = (HETEROGENEITY_THRESHOLDS[nut] ?? FALLBACK_THRESHOLD)[level];
      warnings.push({
        nutrient: nut,
        cv_pct: cvPct == null ? null : round1(cvPct),
        level,
        threshold_pct: threshold,
      });
      if (level === "split") anySplit = true;
      else anyWarn = true;
    }
  }
  if (anySplit) anyWarn = true;

  return {
    cluster_id: cid,
    block_ids: blocks.map((b) => b.block_id),
    block_names: blocks.map((b) => b.block_name),
    total_area_ha: round3(totalArea),
    weight_strategy: useArea ? "area_weighted" : "equal",
    aggregated_targets: aggregated,
    heterogeneity: {
      per_nutrient: perNutrient,
      warnings,
      any_warn: anyWarn,
      any_split: anySplit,
      citation: HETEROGENEITY_CITATION,
    },
  };
}

function collectNutrientKeys(blocks: BlockTargets[]): string[] {
  const seen = new Set<string>();
  for (const b of blocks) {
    for (const k of Object.keys(b.targets)) seen.add(k);
  }
  return Array.from(seen);
}

function weightedMean(values: number[], weights: number[]): number {
  let num = 0;
  let den = 0;
  for (let i = 0; i < values.length; i++) {
    num += values[i] * weights[i];
    den += weights[i];
  }
  if (den === 0) {
    // Equal-weight fallback (shouldn't hit if weights are positive)
    return values.reduce((s, v) => s + v, 0) / values.length;
  }
  return num / den;
}

function sampleCvPct(values: number[], mean: number): number | null {
  if (mean === 0) return null;
  // Sample variance — Bessel's correction (N-1)
  const n = values.length;
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
  const sd = Math.sqrt(variance);
  return (sd / Math.abs(mean)) * 100;
}

function round1(x: number): number {
  return Math.round(x * 10) / 10;
}

function round3(x: number): number {
  return Math.round(x * 1000) / 1000;
}

/** Build a {block_id → cluster_id} map from a server-supplied cluster
 * list. Used to seed the wizard's local assignment state from the
 * preview-schedule response. */
export function assignmentsFromClusters(clusters: ClusterPreview[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const c of clusters) {
    for (const bid of c.block_ids) {
      out[bid] = c.cluster_id;
    }
  }
  return out;
}
