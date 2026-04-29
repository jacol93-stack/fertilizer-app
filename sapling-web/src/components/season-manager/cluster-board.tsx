"use client";

/**
 * Click-driven cluster editor for the wizard's Schedule step.
 *
 * Each block carries a "Move to" dropdown. Each group carries a
 * "Group actions" dropdown (merge into another group, or split every
 * block into its own group). Auto-clustering remains the source of
 * truth — the user only intervenes when an outlier needs handling.
 *
 * Replaced an earlier drag-and-drop implementation that didn't scale
 * past ~10 blocks and had reliability issues with React's
 * dragstart/dragend timing.
 *
 * Dataless blocks (no soil_analysis_id) appear in an "Unassigned" row
 * at the top. Their menu lets you attach them to a group — they get the
 * group's averaged programme at their own area, and an OutstandingItem
 * still flags the missing soil sample on the artifact.
 */

import { useMemo, useState } from "react";
import { Label } from "@/components/ui/label";
import { Plus, MoveRight, MoreHorizontal, Split } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  recomputeClusters,
  computeBlockFits,
  type BlockTargets,
  type BlockFit,
} from "@/lib/cluster-heterogeneity";
import type { ClusterPreview, HeterogeneityWarning } from "@/lib/programmes-v2";

export interface DatalessBlock {
  block_id: string;
  block_name: string;
  block_area_ha: number | null;
}

export interface ClusterBoardProps {
  /** Per-block v2 targets surfaced by the preview-schedule endpoint.
   * Used for client-side heterogeneity recompute on move. */
  blocks: BlockTargets[];
  /** Blocks with no linked soil analysis. Show in the Unassigned row;
   * moving them onto a group attaches via the group's averaged programme. */
  datalessBlocks: DatalessBlock[];
  /** Current block_id → cluster_id assignment map. Drives both the
   * rendered grouping and what the build endpoint sees. */
  assignments: Record<string, string>;
  /** Called whenever the user moves a block (planned or dataless) into
   * a different cluster. Parent updates assignment state + persists in
   * draft. */
  onAssignmentsChange: (next: Record<string, string>) => void;
  /** User's chosen number of groups. When null, the algorithm decides
   * via the heterogeneity threshold path (legacy). When set to a number,
   * the server runs agglomerative clustering and produces exactly k. */
  targetClusters: number | null;
  /** Called when the user picks a different group count. Parent
   * triggers a fresh preview-schedule. */
  onTargetClustersChange: (k: number | null) => void | Promise<void>;
  /** Disabled while a server preview is in flight. */
  busy?: boolean;
  /** Cluster ids currently in use server-side. New clusters created by
   * the user (via "New group" action) get the next free letter. */
  knownClusterIds: string[];
  /** cluster_id → list of method names the user kept selected for this
   * group's blends. Empty / missing key means "use the full intersection".
   * The build sends this as `method_availability_per_cluster`. */
  methodOverridesByCluster: Record<string, string[]>;
  onMethodOverridesChange: (next: Record<string, string[]>) => void;
}

// Method order for stable display + the order method labels render.
const METHOD_ORDER = ["broadcast", "fertigation", "foliar", "side_dress", "band"];

function methodLabel(method: string): string {
  switch (method) {
    case "broadcast":   return "Broadcast";
    case "fertigation": return "Fertigation";
    case "foliar":      return "Foliar";
    case "side_dress":  return "Side dress";
    case "band":        return "Band";
    default:            return method.charAt(0).toUpperCase() + method.slice(1).replace(/_/g, " ");
  }
}

function intersectionOf(arrays: string[][]): string[] {
  if (arrays.length === 0) return [];
  const sets = arrays.map((a) => new Set(a));
  const first = sets[0];
  const out: string[] = [];
  for (const m of METHOD_ORDER) {
    if ([...sets].every((s) => s.has(m))) out.push(m);
  }
  // Catch any non-canonical method that all members happen to share.
  for (const m of first) {
    if (!METHOD_ORDER.includes(m) && [...sets].every((s) => s.has(m))) {
      out.push(m);
    }
  }
  return out;
}

const STATUS_LABEL = {
  ok: {
    pill: "consistent",
    pillClass: "bg-emerald-100 text-emerald-700",
    detail: "All blocks need similar nutrients — one shared programme works.",
  },
  warn: {
    pill: "moderate variability",
    pillClass: "bg-amber-100 text-amber-700",
    detail: "Blocks differ enough that one shared programme is a workable compromise.",
  },
  split: {
    pill: "high variability — consider splitting",
    pillClass: "bg-red-100 text-red-700",
    detail: "Blocks differ enough that one averaged programme will over-fertilise some and under-fertilise others.",
  },
} as const;

function highestStatus(c: ClusterPreview): keyof typeof STATUS_LABEL {
  if (c.heterogeneity.any_split) return "split";
  if (c.heterogeneity.any_warn) return "warn";
  return "ok";
}

function nextClusterId(used: Set<string>): string {
  for (let i = 0; i < 26; i++) {
    const c = String.fromCharCode(65 + i);
    if (!used.has(c)) return c;
  }
  return `Z${used.size}`;
}

export function ClusterBoard(props: ClusterBoardProps) {
  const {
    blocks, datalessBlocks, assignments, onAssignmentsChange,
    targetClusters, onTargetClustersChange,
    busy = false, knownClusterIds,
    methodOverridesByCluster, onMethodOverridesChange,
  } = props;

  // Compute clusters from the committed assignments. No drag-preview
  // overlay anymore — moves commit immediately and the heterogeneity
  // recomputes live.
  const clusters = useMemo(() => {
    const base = recomputeClusters(blocks, assignments);
    if (datalessBlocks.length === 0) return base;
    const out = base.map((c) => ({
      ...c,
      block_ids: [...c.block_ids],
      block_names: [...c.block_names],
    }));
    // Make sure every effective cluster_id exists, even if no
    // targets-bearing block is in it (dataless-only cluster).
    for (const cid of Object.values(assignments)) {
      if (!out.find((c) => c.cluster_id === cid)) {
        out.push({
          cluster_id: cid,
          block_ids: [],
          block_names: [],
          total_area_ha: 0,
          weight_strategy: "equal",
          aggregated_targets: {},
          heterogeneity: {
            per_nutrient: {},
            warnings: [],
            any_warn: false,
            any_split: false,
            citation: "",
          },
        });
      }
    }
    for (const db of datalessBlocks) {
      const assigned = assignments[db.block_id];
      if (!assigned) continue;
      const target = out.find((c) => c.cluster_id === assigned);
      if (target) {
        target.block_ids.push(db.block_id);
        target.block_names.push(db.block_name);
        target.total_area_ha = Math.round(
          (target.total_area_ha + (db.block_area_ha ?? 0)) * 1000,
        ) / 1000;
      }
    }
    return out;
  }, [blocks, assignments, datalessBlocks]);

  // Per-block fits against the clusters they're currently in.
  const blockFits = useMemo(
    () => computeBlockFits(blocks, clusters),
    [blocks, clusters],
  );

  // Set of cluster ids currently in use (committed + server-known).
  // Used for minting fresh ids on "New group".
  const usedClusterIds = useMemo(() => {
    const s = new Set<string>(knownClusterIds);
    for (const id of Object.values(assignments)) s.add(id);
    return s;
  }, [knownClusterIds, assignments]);

  // Dataless blocks not currently attached → "Unassigned" row.
  const unassignedDataless = datalessBlocks.filter((b) => !assignments[b.block_id]);

  // ── Move actions (replace drag) ────────────────────────────────────

  const moveBlockToCluster = (blockId: string, clusterId: string) => {
    if (assignments[blockId] === clusterId) return;
    onAssignmentsChange({ ...assignments, [blockId]: clusterId });
  };

  const moveBlockToNewCluster = (blockId: string) => {
    const newId = nextClusterId(usedClusterIds);
    onAssignmentsChange({ ...assignments, [blockId]: newId });
  };

  const unassignBlock = (blockId: string) => {
    if (!assignments[blockId]) return;
    const next = { ...assignments };
    delete next[blockId];
    onAssignmentsChange(next);
  };

  // Merge: every block currently in `fromId` gets reassigned to `toId`.
  // Doesn't touch dataless blocks that weren't in the source cluster.
  const mergeCluster = (fromId: string, toId: string) => {
    if (fromId === toId) return;
    const next: Record<string, string> = { ...assignments };
    for (const [bid, cid] of Object.entries(assignments)) {
      if (cid === fromId) next[bid] = toId;
    }
    // Also reassign blocks whose only home was the auto-cluster (i.e.
    // they don't appear in `assignments` yet but DO appear in `clusters`
    // under fromId because the server placed them there).
    const cluster = clusters.find((c) => c.cluster_id === fromId);
    if (cluster) {
      for (const bid of cluster.block_ids) {
        if (!(bid in next)) next[bid] = toId;
      }
    }
    onAssignmentsChange(next);
  };

  // Split: every block in `fromId` becomes its own group.
  const splitCluster = (fromId: string) => {
    const cluster = clusters.find((c) => c.cluster_id === fromId);
    if (!cluster) return;
    const next: Record<string, string> = { ...assignments };
    const used = new Set<string>(usedClusterIds);
    let first = true;
    for (const bid of cluster.block_ids) {
      if (first) {
        // Keep the first block in the existing group id so the cluster
        // doesn't disappear out from under the user. The remaining
        // blocks each get a fresh id.
        next[bid] = fromId;
        first = false;
        continue;
      }
      const id = nextClusterId(used);
      used.add(id);
      next[bid] = id;
    }
    onAssignmentsChange(next);
  };

  const groupWord = clusters.length === 1 ? "group" : "groups";
  const totalBlockCount = blocks.length + datalessBlocks.length;
  const otherClusters = (excludeId: string) =>
    clusters.filter((c) => c.cluster_id !== excludeId);

  // Average + worst fit across every block with computed targets.
  // Dataless blocks score 100% by definition (they inherit a recipe);
  // counting them inflates the headline misleadingly, so we exclude
  // them. Singleton clusters always score 100% on every nutrient,
  // which gives the user the right intuition that splitting solves fit.
  const fitSummary = (() => {
    const scored = blocks
      .map((b) => blockFits[b.block_id])
      .filter((f): f is NonNullable<typeof f> => !!f);
    if (scored.length === 0) {
      return { avg: null as number | null, worst: null as null | { name: string; pct: number } };
    }
    const avg = Math.round(
      scored.reduce((s, f) => s + f.overall_pct, 0) / scored.length,
    );
    let worstFit = scored[0];
    for (const f of scored) if (f.overall_pct < worstFit.overall_pct) worstFit = f;
    const block = blocks.find((b) => b.block_id === worstFit.block_id);
    return {
      avg,
      worst: block
        ? { name: block.block_name, pct: Math.round(worstFit.overall_pct) }
        : null,
    };
  })();

  const fitTone = (pct: number | null) => {
    if (pct == null) return "text-muted-foreground";
    if (pct >= 85) return "text-emerald-700";
    if (pct >= 70) return "text-amber-700";
    return "text-red-700";
  };

  return (
    <div className="mb-4 rounded-lg border bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--sapling-dark)]">
            {clusters.length} {groupWord} across {totalBlockCount} block{totalBlockCount !== 1 ? "s" : ""}
          </p>
          {fitSummary.avg != null && (
            <p className="mt-0.5 text-xs">
              <span className="text-muted-foreground">Average fit </span>
              <span className={`font-semibold ${fitTone(fitSummary.avg)}`}>
                {fitSummary.avg}%
              </span>
              {fitSummary.worst && (
                <>
                  <span className="text-muted-foreground"> · worst </span>
                  <span className={`font-semibold ${fitTone(fitSummary.worst.pct)}`}>
                    {fitSummary.worst.pct}%
                  </span>
                  <span className="text-muted-foreground"> ({fitSummary.worst.name})</span>
                </>
              )}
            </p>
          )}
          <p className="mt-0.5 text-xs text-muted-foreground">
            Pick how many groups you want to mix this season — the system finds the
            tightest split. Use Move / Group actions to override per block.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="cluster-target-k" className="text-xs text-muted-foreground">
            Number of groups
          </Label>
          <select
            id="cluster-target-k"
            value={targetClusters ?? ""}
            disabled={busy || totalBlockCount === 0}
            onChange={(e) => {
              const v = e.target.value;
              onTargetClustersChange(v === "" ? null : parseInt(v, 10));
            }}
            className="rounded-md border bg-white px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
            title="Pick how many programmes you want to mix this season. The system will produce the agronomically tightest split at that group count."
          >
            <option value="">Auto</option>
            {Array.from({ length: Math.max(1, totalBlockCount) }, (_, i) => i + 1).map((k) => (
              <option key={k} value={k}>
                {k} {k === 1 ? "group" : "groups"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Unassigned (dataless) row */}
      {unassignedDataless.length > 0 && (
        <div className="mb-3 rounded-md border border-dashed bg-amber-50/60 p-3">
          <p className="mb-2 text-xs font-medium text-amber-800">
            Unassigned — no soil analysis ({unassignedDataless.length})
          </p>
          <p className="mb-2 text-xs text-amber-700">
            Pick a group from the Move menu to apply a rough plan based on that
            group&apos;s averaged targets. The block will still be flagged as
            needing a soil analysis.
          </p>
          <div className="flex flex-wrap gap-2">
            {unassignedDataless.map((db) => (
              <BlockChip
                key={db.block_id}
                blockName={db.block_name}
                area={db.block_area_ha}
                dataless
                fit={null}
                clusters={clusters}
                onMoveTo={(cid) => moveBlockToCluster(db.block_id, cid)}
                onMoveToNew={() => moveBlockToNewCluster(db.block_id)}
                onUnassign={null}
              />
            ))}
          </div>
        </div>
      )}

      {/* Cluster cards. */}
      <div className="space-y-2">
        {clusters.map((c) => {
          const status = highestStatus(c);
          const label = STATUS_LABEL[status];
          const others = otherClusters(c.cluster_id);
          const canSplit = c.block_ids.length > 1;
          return (
            <div
              key={c.cluster_id}
              className="rounded-md border bg-muted/20 p-3"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-[var(--sapling-dark)]">
                    Group {c.cluster_id}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {c.total_area_ha} ha · {c.block_names.length} block
                    {c.block_names.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${label.pillClass}`}
                    title={label.detail}
                  >
                    {label.pill}
                  </span>
                  {(others.length > 0 || canSplit) && (
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        className="rounded p-1 text-muted-foreground hover:bg-white hover:text-[var(--sapling-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
                        title="Group actions"
                      >
                        <MoreHorizontal className="size-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="min-w-44">
                        {others.length > 0 && (
                          <DropdownMenuGroup>
                            <DropdownMenuLabel>Merge into…</DropdownMenuLabel>
                            {others.map((o) => (
                              <DropdownMenuItem
                                key={o.cluster_id}
                                onClick={() => mergeCluster(c.cluster_id, o.cluster_id)}
                              >
                                Group {o.cluster_id}
                                <span className="ml-2 text-xs text-muted-foreground">
                                  {o.block_ids.length} block{o.block_ids.length === 1 ? "" : "s"}
                                </span>
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuGroup>
                        )}
                        {canSplit && (
                          <>
                            {others.length > 0 && <DropdownMenuSeparator />}
                            <DropdownMenuGroup>
                              <DropdownMenuItem onClick={() => splitCluster(c.cluster_id)}>
                                <Split className="mr-2 size-3.5" />
                                Split: each block its own group
                              </DropdownMenuItem>
                            </DropdownMenuGroup>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{label.detail}</p>

              {/* Block chips inside this cluster */}
              <div className="mt-2 flex flex-wrap gap-2">
                {c.block_ids.map((bid, idx) => {
                  const blockName = c.block_names[idx];
                  const blockMeta = blocks.find((b) => b.block_id === bid);
                  const datalessMeta = datalessBlocks.find((d) => d.block_id === bid);
                  const isDataless = !!datalessMeta && !blockMeta;
                  return (
                    <BlockChip
                      key={bid}
                      blockName={blockName}
                      area={blockMeta?.block_area_ha ?? datalessMeta?.block_area_ha ?? null}
                      dataless={isDataless}
                      fit={blockFits[bid] ?? null}
                      clusters={others}
                      acceptedMethods={blockMeta?.accepted_methods}
                      onMoveTo={(cid) => moveBlockToCluster(bid, cid)}
                      onMoveToNew={() => moveBlockToNewCluster(bid)}
                      onUnassign={isDataless ? () => unassignBlock(bid) : null}
                    />
                  );
                })}
              </div>

              {/* Per-nutrient warnings */}
              {c.heterogeneity.warnings.length > 0 && (
                <ul className="mt-2 space-y-0.5 text-xs">
                  {c.heterogeneity.warnings.map((w) => (
                    <WarningLine key={w.nutrient} warning={w} />
                  ))}
                </ul>
              )}

              {/* Methods — block-level capability + group intersection.
                  The user can untick methods from the intersection to
                  scope this season's blends; engine receives the
                  result on `method_availability_per_cluster`. */}
              <MethodsPanel
                cluster={c}
                blocks={blocks}
                datalessBlocks={datalessBlocks}
                override={methodOverridesByCluster[c.cluster_id] ?? null}
                onChange={(next) => {
                  const updated = { ...methodOverridesByCluster };
                  if (next === null) delete updated[c.cluster_id];
                  else updated[c.cluster_id] = next;
                  onMethodOverridesChange(updated);
                }}
              />

              {/* Per-block consequences — shows the agronomic cost of
                  this grouping in real nutrient terms. Surfaces only
                  when at least one block in the group fits below the
                  85% green band. */}
              <ConsequencesPanel cluster={c} blocks={blocks} blockFits={blockFits} />
            </div>
          );
        })}
      </div>

      {/* Citation lives in code comments + admin-mode artifact for
          audit; agronomist-facing UI stays clean. */}
    </div>
  );
}

interface BlockChipProps {
  blockName: string;
  area: number | null;
  dataless?: boolean;
  fit: BlockFit | null;
  clusters: ClusterPreview[];
  /** Methods this block's field record supports. Rendered as small
   * text chips below the name so the user can see which blocks limit
   * the group's intersection. Empty / undefined means "unknown" — the
   * preview-schedule resolution should always populate this. */
  acceptedMethods?: string[];
  onMoveTo: (clusterId: string) => void;
  onMoveToNew: () => void;
  /** When non-null, exposes "Unassign" — used for dataless chips that
   * the user wants to take back out of a group. */
  onUnassign: (() => void) | null;
}

function fitColor(pct: number): string {
  if (pct >= 85) return "bg-emerald-500";
  if (pct >= 70) return "bg-amber-500";
  return "bg-red-500";
}

function fitTextColor(pct: number): string {
  if (pct >= 85) return "text-emerald-700";
  if (pct >= 70) return "text-amber-700";
  return "text-red-700";
}

function BlockChip({
  blockName, area, dataless, fit, clusters, acceptedMethods,
  onMoveTo, onMoveToNew, onUnassign,
}: BlockChipProps) {
  const showFit = fit && !dataless;
  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs ${
        dataless
          ? "border-amber-300 bg-amber-100/60 text-amber-900"
          : "border-gray-200 bg-white text-[var(--sapling-dark)]"
      }`}
    >
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <span className="font-medium">{blockName}</span>
          {area != null && (
            <span className="text-[10px] text-muted-foreground">{area} ha</span>
          )}
          {dataless && (
            <span className="text-[10px] uppercase tracking-wide text-amber-700">no soil</span>
          )}
        </div>
        {acceptedMethods && acceptedMethods.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {acceptedMethods.map((m) => (
              <span
                key={m}
                className="rounded-sm bg-gray-100 px-1 py-px text-[9px] uppercase tracking-wide text-gray-600"
                title={`This block supports ${methodLabel(m)} application`}
              >
                {methodLabel(m)}
              </span>
            ))}
          </div>
        )}
        {showFit && fit && <FitBar fit={fit} />}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger
          className="ml-1 rounded p-0.5 text-muted-foreground hover:bg-gray-100 hover:text-[var(--sapling-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
          title="Move to another group"
        >
          <MoveRight className="size-3.5" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-44">
          <DropdownMenuGroup>
            <DropdownMenuLabel>Move to…</DropdownMenuLabel>
            {clusters.length === 0 && (
              <DropdownMenuItem disabled>(no other groups)</DropdownMenuItem>
            )}
            {clusters.map((c) => (
              <DropdownMenuItem
                key={c.cluster_id}
                onClick={() => onMoveTo(c.cluster_id)}
              >
                Group {c.cluster_id}
                <span className="ml-2 text-xs text-muted-foreground">
                  {c.block_ids.length} block{c.block_ids.length === 1 ? "" : "s"}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem onClick={onMoveToNew}>
              <Plus className="mr-2 size-3.5" />
              New group
            </DropdownMenuItem>
          </DropdownMenuGroup>
          {onUnassign && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem onClick={onUnassign}>
                  Unassign (back to no-soil row)
                </DropdownMenuItem>
              </DropdownMenuGroup>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

function FitBar({ fit }: { fit: BlockFit }) {
  const pct = Math.round(fit.overall_pct);
  const worst = fit.worst_nutrient && fit.worst_pct != null
    ? `worst: ${fit.worst_nutrient} ${Math.round(fit.worst_pct)}%`
    : null;
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex h-1 w-14 overflow-hidden rounded-full bg-gray-200">
        <div
          className={`${fitColor(fit.overall_pct)} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[10px] font-medium ${fitTextColor(fit.overall_pct)}`}>
        {pct}% fit
      </span>
      {worst && (
        <span className="text-[10px] text-muted-foreground">· {worst}</span>
      )}
    </div>
  );
}

function WarningLine({ warning }: { warning: HeterogeneityWarning }) {
  return (
    <li className="text-muted-foreground">
      <span className="font-medium text-[var(--sapling-dark)]">{warning.nutrient}</span>{" "}
      CV {warning.cv_pct ?? "—"}%
      {" "}
      <span className={warning.level === "split" ? "text-red-600" : "text-amber-600"}>
        ({warning.level === "split" ? "exceeds split threshold" : "above warn threshold"} — {warning.threshold_pct}%)
      </span>
    </li>
  );
}

// ── Consequences panel ────────────────────────────────────────────────
// Shows what this grouping costs agronomically: per-block over/under
// in nutrient terms, ordered worst-fit first. Only renders when at
// least one block in the group is below the 85% "green" band — a
// well-fitting cluster doesn't need a consequence list.

const FIT_GREEN_BAND = 85;
const FIT_AMBER_BAND = 70;

// ── Methods panel ──────────────────────────────────────────────────
//
// Block-level methods are the source of truth. A group's blends can
// only use methods that EVERY member supports — the intersection. The
// user can untick methods from that intersection to scope this season
// (e.g. "fertigation only on Group A even though they have broadcast
// gear too"). When the intersection is empty, that's a hard error —
// the group as composed has no method in common.

function MethodsPanel({
  cluster, blocks, datalessBlocks, override, onChange,
}: {
  cluster: ClusterPreview;
  blocks: BlockTargets[];
  datalessBlocks: DatalessBlock[];
  override: string[] | null;
  onChange: (next: string[] | null) => void;
}) {
  // Member methods — dataless blocks have no field record so they
  // contribute no method constraint (they inherit the group's pick).
  const memberMethods: string[][] = [];
  for (const bid of cluster.block_ids) {
    const meta = blocks.find((b) => b.block_id === bid);
    if (meta?.accepted_methods && meta.accepted_methods.length > 0) {
      memberMethods.push(meta.accepted_methods);
    }
  }

  const intersection = memberMethods.length > 0
    ? intersectionOf(memberMethods)
    : [];

  // Detect blocks that contribute nothing to the intersection — i.e.
  // blocks whose own methods are a subset that's already empty after
  // ANDing the others. Surfaces the offender so the user can fix.
  const offenders: string[] = [];
  if (memberMethods.length > 1 && intersection.length === 0) {
    for (const bid of cluster.block_ids) {
      const meta = blocks.find((b) => b.block_id === bid);
      const methods = meta?.accepted_methods ?? [];
      if (methods.length === 0) {
        // dataless or method-less; not an offender
        continue;
      }
      // A block is an offender if removing it would leave a non-empty
      // intersection across the remaining members.
      const others = memberMethods.filter((m) => m !== methods);
      if (others.length > 0 && intersectionOf(others).length > 0) {
        offenders.push(meta?.block_name ?? bid);
      }
    }
  }

  // Effective selection — override clamped to current intersection.
  const effective = override
    ? override.filter((m) => intersection.includes(m))
    : intersection;

  const toggleMethod = (method: string) => {
    const next = effective.includes(method)
      ? effective.filter((m) => m !== method)
      : [...effective, method];
    // If the user picks the full intersection, clear the override so
    // future membership changes auto-track the intersection again.
    if (next.length === intersection.length && next.every((m) => intersection.includes(m))) {
      onChange(null);
    } else {
      onChange(next);
    }
  };

  if (intersection.length === 0 && memberMethods.length > 0) {
    return (
      <div className="mt-2 rounded-md border border-red-300 bg-red-50/50 px-3 py-2 text-xs text-red-900">
        <p className="font-medium">No application methods shared across this group.</p>
        <p className="mt-0.5">
          {offenders.length > 0
            ? `${offenders.join(", ")} doesn't share a method with the rest. `
            : "Member blocks have no method in common. "}
          Move the offending block to another group or update its capability on the field record.
        </p>
      </div>
    );
  }

  if (memberMethods.length === 0) {
    return null;
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Methods this group will use
      </span>
      <div className="flex flex-wrap gap-1">
        {intersection.map((m) => {
          const active = effective.includes(m);
          return (
            <button
              key={m}
              type="button"
              onClick={() => toggleMethod(m)}
              className={`rounded-md border px-2 py-0.5 text-xs transition-colors ${
                active
                  ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                  : "border-gray-200 bg-white text-muted-foreground line-through hover:border-gray-300"
              }`}
              title={
                active
                  ? `Click to exclude ${methodLabel(m)} from this group's blends this season`
                  : `Click to re-enable ${methodLabel(m)}`
              }
            >
              {methodLabel(m)}
            </button>
          );
        })}
      </div>
      {effective.length === 0 && (
        <span className="text-[10px] text-red-700">
          No methods selected — at least one must stay enabled to build this group's blends.
        </span>
      )}
    </div>
  );
}

function ConsequencesPanel({
  cluster, blocks, blockFits,
}: {
  cluster: ClusterPreview;
  blocks: BlockTargets[];
  blockFits: Record<string, BlockFit>;
}) {
  const [expanded, setExpanded] = useState(false);

  // Build per-block consequence rows for blocks scored against this
  // cluster's averaged programme. Dataless blocks aren't scored.
  type Row = {
    blockId: string;
    blockName: string;
    overall: number;
    deltas: Array<{ nutrient: string; blockTarget: number; clusterAvg: number; pct: number }>;
  };

  const rows: Row[] = [];
  for (const bid of cluster.block_ids) {
    const fit = blockFits[bid];
    const block = blocks.find((b) => b.block_id === bid);
    if (!fit || !block) continue;
    const deltas: Row["deltas"] = [];
    for (const [nut, blockVal] of Object.entries(block.targets)) {
      const avg = cluster.aggregated_targets[nut];
      if (typeof avg !== "number" || typeof blockVal !== "number") continue;
      if (Math.abs(avg) < 0.01) continue;
      const pct = ((blockVal - avg) / Math.abs(avg)) * 100;
      // Surface only the meaningful gaps (≥ 5 %) to keep the list useful.
      if (Math.abs(pct) >= 5) {
        deltas.push({ nutrient: nut, blockTarget: blockVal, clusterAvg: avg, pct });
      }
    }
    // Worst-deviation nutrient first within each block.
    deltas.sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));
    rows.push({
      blockId: bid,
      blockName: block.block_name,
      overall: fit.overall_pct,
      deltas,
    });
  }

  // Worst-fit blocks first.
  rows.sort((a, b) => a.overall - b.overall);

  const hasMisfit = rows.some((r) => r.overall < FIT_GREEN_BAND);
  if (!hasMisfit || rows.length === 0) return null;

  const summary = (() => {
    const bad = rows.filter((r) => r.overall < FIT_AMBER_BAND).length;
    const meh = rows.filter((r) => r.overall >= FIT_AMBER_BAND && r.overall < FIT_GREEN_BAND).length;
    if (bad > 0) return `${bad} block${bad === 1 ? "" : "s"} fit below 70%`;
    return `${meh} block${meh === 1 ? "" : "s"} fit 70–85%`;
  })();

  return (
    <div className="mt-2 rounded-md border border-amber-200 bg-amber-50/30">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-xs font-medium text-amber-900 hover:bg-amber-50"
      >
        <span>Consequences for this grouping — {summary}</span>
        <span className="text-amber-700">{expanded ? "Hide" : "Show details"}</span>
      </button>
      {expanded && (
        <div className="border-t border-amber-200 px-3 py-2">
          <ul className="space-y-2 text-xs">
            {rows.map((r) => (
              <li key={r.blockId}>
                <p className="font-medium text-[var(--sapling-dark)]">
                  {r.blockName}
                  <span className={`ml-2 font-semibold ${
                    r.overall >= FIT_GREEN_BAND
                      ? "text-emerald-700"
                      : r.overall >= FIT_AMBER_BAND
                        ? "text-amber-700"
                        : "text-red-700"
                  }`}>
                    {Math.round(r.overall)}% fit
                  </span>
                </p>
                {r.deltas.length === 0 ? (
                  <p className="text-muted-foreground">All nutrients within 5% of the group's averaged programme.</p>
                ) : (
                  <ul className="mt-0.5 space-y-0.5 pl-3">
                    {r.deltas.slice(0, 4).map((d) => {
                      // pct = (block_target - cluster_avg) / |cluster_avg| × 100.
                      //   pct < 0 → block needs LESS than the programme delivers
                      //             → programme over-supplies this block.
                      //   pct > 0 → block needs MORE than the programme delivers
                      //             → programme under-supplies this block.
                      // Under-supply is the higher agronomic risk (yield /
                      // quality loss) so it gets red; over-supply is amber.
                      const isOver = d.pct < 0;
                      const magnitude = Math.abs(Math.round(d.pct));
                      return (
                        <li key={d.nutrient} className="text-muted-foreground">
                          <span className="font-medium text-[var(--sapling-dark)]">{d.nutrient}</span>{" "}
                          — programme delivers <span className="tabular-nums">{d.clusterAvg.toFixed(1)}</span> kg/ha,
                          block needs <span className="tabular-nums">{d.blockTarget.toFixed(1)}</span> kg/ha
                          <span className={isOver ? " text-amber-700" : " text-red-700"}>
                            {" "}({magnitude}% {isOver ? "over" : "short"})
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
