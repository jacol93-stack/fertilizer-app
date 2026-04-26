"use client";

/**
 * Drag-and-drop cluster editor for the wizard's Schedule step.
 *
 * Each cluster card is a drop zone; block chips are draggable. Dragging a
 * block to a different cluster updates the local assignment map and
 * recomputes heterogeneity in-place via cluster-heterogeneity.ts. No API
 * round-trip until the user advances to step 3 (the build sends the final
 * cluster_assignments dict).
 *
 * Dataless blocks (no soil_analysis_id) appear in an "Unassigned" row at
 * the top. Dropping them onto a cluster card attaches them via the
 * SkippedBlockRequest.attach_to_cluster mechanism — they get the cluster's
 * averaged recipe at their own area, and an OutstandingItem still flags
 * the missing soil sample.
 *
 * The threshold dropdown (cluster margin) re-runs preview-schedule when
 * changed — that's the only flow that goes back to the server while
 * editing.
 */

import { useMemo, useRef, useState } from "react";
import { Label } from "@/components/ui/label";
import { Plus } from "lucide-react";
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
   * Used for client-side heterogeneity recompute on drop. */
  blocks: BlockTargets[];
  /** Blocks with no linked soil analysis. Show in the Unassigned row;
   * dropping them onto a cluster attaches via the cluster's averaged recipe. */
  datalessBlocks: DatalessBlock[];
  /** Current block_id → cluster_id assignment map. Drives both the
   * rendered grouping and what the build endpoint sees. */
  assignments: Record<string, string>;
  /** Called whenever the user drops a block (planned or dataless) into a
   * cluster. Parent updates assignment state + persists in draft. */
  onAssignmentsChange: (next: Record<string, string>) => void;
  /** Cluster margin (NPK-distance threshold). Changing it re-runs the
   * preview-schedule on the server because the auto-grouping changes. */
  margin: number;
  onMarginChange: (m: number) => void | Promise<void>;
  /** Disabled while a server preview is in flight (margin change). */
  busy?: boolean;
  /** Cluster ids currently in use server-side. New clusters created by
   * the user (drop into "+ New Recipe") get the next free letter. */
  knownClusterIds: string[];
  /** Show the per-build threshold override dropdown? Admin-only — non-
   * admins always run on the app-wide default set in admin settings. */
  showMarginControl?: boolean;
}

const STATUS_LABEL = {
  ok: {
    pill: "consistent",
    pillClass: "bg-emerald-100 text-emerald-700",
    detail: "All blocks need similar nutrients — one recipe works.",
  },
  warn: {
    pill: "moderate variability",
    pillClass: "bg-amber-100 text-amber-700",
    detail: "Blocks differ enough that one recipe is a workable compromise.",
  },
  split: {
    pill: "high variability — consider splitting",
    pillClass: "bg-red-100 text-red-700",
    detail: "Blocks differ enough that one averaged recipe will over-fertilise some and under-fertilise others.",
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
    margin, onMarginChange, busy = false, knownClusterIds,
    showMarginControl = false,
  } = props;

  // Ref-of-truth so handlers don't depend on a re-render that the
  // browser's drag session may have aborted. State copy drives the
  // ghost-preview render only.
  const draggedBlockIdRef = useRef<string | null>(null);
  const [draggedBlockId, setDraggedBlockId] = useState<string | null>(null);
  const [hoverClusterId, setHoverClusterId] = useState<string | null>(null);

  // Single source of truth: render whatever assignments WOULD be in
  // effect right now, including any in-flight drag preview. After a
  // drop the preview clears and assignments are the committed state.
  const effectiveAssignments = useMemo(() => {
    if (!draggedBlockId || !hoverClusterId) return assignments;
    if (hoverClusterId === "__new__") {
      // Mid-drag over the "+ New Recipe" zone: assign to the next free
      // letter so a Recipe X card materialises in real time.
      const used = new Set<string>(knownClusterIds);
      for (const id of Object.values(assignments)) used.add(id);
      const newId = nextClusterId(used);
      if (assignments[draggedBlockId] === newId) return assignments;
      return { ...assignments, [draggedBlockId]: newId };
    }
    if (assignments[draggedBlockId] === hoverClusterId) return assignments;
    return { ...assignments, [draggedBlockId]: hoverClusterId };
  }, [assignments, draggedBlockId, hoverClusterId, knownClusterIds]);

  const previewing = effectiveAssignments !== assignments;

  // Compute clusters from the effective (possibly preview) assignments,
  // overlay dataless blocks afterwards. This is the ONLY rendering
  // source — no split between base and preview.
  const clusters = useMemo(() => {
    const base = recomputeClusters(blocks, effectiveAssignments);
    if (datalessBlocks.length === 0) return base;
    const out = base.map((c) => ({
      ...c,
      block_ids: [...c.block_ids],
      block_names: [...c.block_names],
    }));
    // Make sure every effective cluster_id exists, even if no
    // targets-bearing block is in it (dataless-only cluster).
    for (const cid of Object.values(effectiveAssignments)) {
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
      const assigned = effectiveAssignments[db.block_id];
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
  }, [blocks, effectiveAssignments, datalessBlocks]);

  // Per-block fits against the clusters they're currently in (or
  // would be in if the drag commits).
  const blockFits = useMemo(
    () => computeBlockFits(blocks, clusters),
    [blocks, clusters],
  );

  // For "→" arrow: cluster ids whose heterogeneity differs from the
  // committed (non-preview) state. When previewing, compare the live
  // recipe's any_warn/any_split against what it'd be without the drag.
  const baselineStatusByCluster = useMemo(() => {
    if (!previewing) return null;
    const baseline = recomputeClusters(blocks, assignments);
    const m: Record<string, "ok" | "warn" | "split"> = {};
    for (const c of baseline) {
      m[c.cluster_id] = c.heterogeneity.any_split
        ? "split"
        : c.heterogeneity.any_warn ? "warn" : "ok";
    }
    return m;
  }, [previewing, blocks, assignments]);

  // For minting fresh recipe ids on drop. Built from the COMMITTED
  // assignments only — never from `clusters` (which can include the
  // in-flight drag preview's hypothetical id and would cause the next
  // letter to skip).
  const committedUsedIds = useMemo(() => {
    const s = new Set<string>(knownClusterIds);
    for (const id of Object.values(assignments)) s.add(id);
    return s;
  }, [knownClusterIds, assignments]);

  // Dataless blocks not currently attached → "Unassigned" row.
  const unassignedDataless = datalessBlocks.filter((b) => !assignments[b.block_id]);

  const handleDragStart = (blockId: string) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", blockId);
    draggedBlockIdRef.current = blockId;
    // Defer state update to next frame — setting state synchronously
    // here can trigger a React re-render that aborts the browser's
    // drag session before it stabilises.
    requestAnimationFrame(() => setDraggedBlockId(blockId));
  };

  const handleDragEnd = () => {
    draggedBlockIdRef.current = null;
    setDraggedBlockId(null);
    setHoverClusterId(null);
  };

  const handleDragOver = (clusterId: string) => (e: React.DragEvent) => {
    // preventDefault on EVERY dragOver is required for drop to fire.
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (hoverClusterId !== clusterId) setHoverClusterId(clusterId);
  };

  const handleDragLeave = (clusterId: string) => (e: React.DragEvent) => {
    // Without this guard, dragLeave fires every time the cursor crosses
    // a child element (chip / fit-bar / text), flickering the hover
    // state. relatedTarget tells us where the cursor went next — if
    // it's still inside this drop zone, ignore.
    const next = e.relatedTarget as Node | null;
    if (next && (e.currentTarget as Node).contains(next)) return;
    if (hoverClusterId === clusterId) setHoverClusterId(null);
  };

  const readDroppedBlockId = (e: React.DragEvent): string | null => {
    return e.dataTransfer.getData("text/plain") || draggedBlockIdRef.current;
  };

  const handleDrop = (clusterId: string) => (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const blockId = readDroppedBlockId(e);
    if (!blockId) return;
    if (assignments[blockId] !== clusterId) {
      onAssignmentsChange({ ...assignments, [blockId]: clusterId });
    }
    draggedBlockIdRef.current = null;
    setDraggedBlockId(null);
    setHoverClusterId(null);
  };

  const handleNewClusterDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const blockId = readDroppedBlockId(e);
    if (!blockId) return;
    const newId = nextClusterId(committedUsedIds);
    onAssignmentsChange({ ...assignments, [blockId]: newId });
    draggedBlockIdRef.current = null;
    setDraggedBlockId(null);
    setHoverClusterId(null);
  };

  const recipeWord = clusters.length === 1 ? "recipe" : "recipes";
  const totalBlockCount = blocks.length + datalessBlocks.length;

  return (
    <div className="mb-4 rounded-lg border bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--sapling-dark)]">
            {clusters.length} {recipeWord} across {totalBlockCount} block{totalBlockCount !== 1 ? "s" : ""}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Drag blocks between recipes to override the auto-grouping. Each recipe
            is one batch the farmer mixes; per-block rates differ within a recipe.
          </p>
        </div>
        {showMarginControl && (
          <div className="flex items-center gap-2">
            <Label htmlFor="cluster-margin" className="text-xs text-muted-foreground">
              Auto-group threshold
            </Label>
            <select
              id="cluster-margin"
              value={margin}
              disabled={busy}
              onChange={(e) => onMarginChange(parseFloat(e.target.value))}
              className="rounded-md border bg-white px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
            >
              <option value={0.10}>0.10 (tight)</option>
              <option value={0.15}>0.15</option>
              <option value={0.20}>0.20</option>
              <option value={0.25}>0.25 (default)</option>
              <option value={0.30}>0.30</option>
              <option value={0.40}>0.40 (loose)</option>
            </select>
          </div>
        )}
      </div>

      {/* Unassigned (dataless) row */}
      {unassignedDataless.length > 0 && (
        <div className="mb-3 rounded-md border border-dashed bg-amber-50/60 p-3">
          <p className="mb-2 text-xs font-medium text-amber-800">
            Unassigned — no soil analysis ({unassignedDataless.length})
          </p>
          <p className="mb-2 text-xs text-amber-700">
            Drag onto a recipe to apply a rough plan based on that recipe&apos;s averaged targets.
            The block will still be flagged as needing a soil analysis.
          </p>
          <div className="flex flex-wrap gap-2">
            {unassignedDataless.map((db) => (
              <BlockChip
                key={db.block_id}
                blockName={db.block_name}
                area={db.block_area_ha}
                dataless
                onDragStart={handleDragStart(db.block_id)}
                onDragEnd={handleDragEnd}
              />
            ))}
          </div>
        </div>
      )}

      {/* Cluster cards. Single source of truth: `clusters` is computed
          from effectiveAssignments which already includes any in-flight
          drag preview. Cards appear/disappear in real time as the user
          drags. */}
      <div className="space-y-2">
        {clusters.map((c) => {
          const status = highestStatus(c);
          const baseline = baselineStatusByCluster?.[c.cluster_id] ?? status;
          const arrowChange = previewing && baseline !== status;
          const label = STATUS_LABEL[status];
          const isHover = hoverClusterId === c.cluster_id;
          // Set of block ids that are NOT in this cluster in the
          // committed (non-preview) assignment — i.e. ghost previews.
          const ghostIds = new Set<string>();
          if (previewing && draggedBlockId && effectiveAssignments[draggedBlockId] === c.cluster_id) {
            if (assignments[draggedBlockId] !== c.cluster_id) {
              ghostIds.add(draggedBlockId);
            }
          }
          return (
            <div
              key={c.cluster_id}
              onDragOver={handleDragOver(c.cluster_id)}
              onDragLeave={handleDragLeave(c.cluster_id)}
              onDrop={handleDrop(c.cluster_id)}
              className={`rounded-md border-2 p-3 transition-colors ${
                isHover
                  ? "border-[var(--sapling-orange)] bg-orange-50/40"
                  : "border-transparent bg-muted/20"
              }`}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-[var(--sapling-dark)]">
                    Recipe {c.cluster_id}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {c.total_area_ha} ha · {c.block_names.length} block
                    {c.block_names.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${label.pillClass}`}
                  title={label.detail}
                >
                  {arrowChange && "→ "}
                  {label.pill}
                </span>
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
                      onDragStart={handleDragStart(bid)}
                      onDragEnd={handleDragEnd}
                      ghostPreview={ghostIds.has(bid)}
                      fit={blockFits[bid] ?? null}
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

              {arrowChange && status === "split" && baseline !== "split" && (
                <p className="mt-2 rounded border border-red-300 bg-red-50 p-2 text-xs text-red-800">
                  This move pushes Recipe {c.cluster_id} past the published
                  heterogeneity threshold (Wilding 1985). The averaged recipe
                  will over- or under-fertilise some blocks.
                </p>
              )}
            </div>
          );
        })}

        {/* "+ New Recipe" drop zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
            setHoverClusterId("__new__");
          }}
          onDragLeave={() => {
            if (hoverClusterId === "__new__") setHoverClusterId(null);
          }}
          onDrop={handleNewClusterDrop}
          className={`flex items-center justify-center gap-2 rounded-md border-2 border-dashed py-3 text-xs ${
            hoverClusterId === "__new__"
              ? "border-[var(--sapling-orange)] bg-orange-50/40 text-[var(--sapling-orange)]"
              : "border-muted-foreground/30 text-muted-foreground"
          }`}
        >
          <Plus className="size-3" />
          Drop here to start a new recipe
        </div>
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
  ghostPreview?: boolean;
  fit?: BlockFit | null;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
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

function BlockChip({ blockName, area, dataless, ghostPreview, fit, onDragStart, onDragEnd }: BlockChipProps) {
  const showFit = fit && !dataless;
  const tooltip = buildChipTooltip({ dataless, fit });
  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      title={tooltip}
      className={`inline-flex cursor-grab select-none flex-col gap-0.5 rounded-md border px-2.5 py-1.5 text-xs active:cursor-grabbing ${
        ghostPreview
          ? "border-dashed border-[var(--sapling-orange)] bg-orange-50/50 text-[var(--sapling-orange)]"
          : dataless
            ? "border-amber-300 bg-amber-100/60 text-amber-900"
            : "border-gray-200 bg-white text-[var(--sapling-dark)]"
      }`}
    >
      <div className="flex items-center gap-1.5">
        <span className="font-medium">{blockName}</span>
        {area != null && (
          <span className="text-[10px] text-muted-foreground">{area} ha</span>
        )}
        {dataless && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">no soil</span>
        )}
      </div>
      {showFit && (
        <FitBar fit={fit} />
      )}
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

function buildChipTooltip(args: { dataless?: boolean; fit?: BlockFit | null }): string {
  if (args.dataless) {
    return "No soil analysis — drag onto a recipe to apply a rough plan.";
  }
  if (!args.fit) return "Drag to reassign";
  const lines = ["Drag to reassign", "", "Fit vs current recipe:"];
  for (const [nut, pct] of Object.entries(args.fit.per_nutrient)) {
    const marker = nut === args.fit.worst_nutrient ? " ← worst" : "";
    lines.push(`  ${nut}: ${Math.round(pct)}%${marker}`);
  }
  return lines.join("\n");
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
