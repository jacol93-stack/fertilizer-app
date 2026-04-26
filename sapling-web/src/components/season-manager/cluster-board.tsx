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

import { useMemo, useState } from "react";
import { Label } from "@/components/ui/label";
import { Plus } from "lucide-react";
import {
  recomputeClusters,
  type BlockTargets,
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
  } = props;

  const [draggedBlockId, setDraggedBlockId] = useState<string | null>(null);
  const [hoverClusterId, setHoverClusterId] = useState<string | null>(null);

  // Recompute clusters from current assignments. Identity-stable per
  // assignments dict so React doesn't re-render unnecessarily.
  const clusters = useMemo(
    () => recomputeClusters(blocks, assignments),
    [blocks, assignments],
  );

  // Preview clusters: what would the heterogeneity look like if the
  // currently-dragged block landed in hoverClusterId?
  const previewClusters = useMemo(() => {
    if (!draggedBlockId || !hoverClusterId) return null;
    if (assignments[draggedBlockId] === hoverClusterId) return null;
    const next = { ...assignments, [draggedBlockId]: hoverClusterId };
    return recomputeClusters(blocks, next);
  }, [draggedBlockId, hoverClusterId, assignments, blocks]);

  const previewByClusterId = useMemo(() => {
    const m: Record<string, ClusterPreview> = {};
    if (previewClusters) {
      for (const p of previewClusters) m[p.cluster_id] = p;
    }
    return m;
  }, [previewClusters]);

  const allUsedIds = useMemo(() => {
    const s = new Set<string>(knownClusterIds);
    for (const c of clusters) s.add(c.cluster_id);
    for (const id of Object.values(assignments)) s.add(id);
    return s;
  }, [knownClusterIds, clusters, assignments]);

  // Dataless blocks not currently attached → "Unassigned" row.
  const unassignedDataless = datalessBlocks.filter((b) => !assignments[b.block_id]);

  const handleDragStart = (blockId: string) => (e: React.DragEvent) => {
    setDraggedBlockId(blockId);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", blockId); // Required for some browsers
  };

  const handleDragEnd = () => {
    setDraggedBlockId(null);
    setHoverClusterId(null);
  };

  const handleDragOver = (clusterId: string) => (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (hoverClusterId !== clusterId) setHoverClusterId(clusterId);
  };

  const handleDragLeave = (clusterId: string) => () => {
    if (hoverClusterId === clusterId) setHoverClusterId(null);
  };

  const handleDrop = (clusterId: string) => (e: React.DragEvent) => {
    e.preventDefault();
    const blockId = e.dataTransfer.getData("text/plain") || draggedBlockId;
    if (!blockId) return;
    if (assignments[blockId] === clusterId) return;
    onAssignmentsChange({ ...assignments, [blockId]: clusterId });
    setDraggedBlockId(null);
    setHoverClusterId(null);
  };

  const handleNewClusterDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const blockId = e.dataTransfer.getData("text/plain") || draggedBlockId;
    if (!blockId) return;
    const newId = nextClusterId(allUsedIds);
    onAssignmentsChange({ ...assignments, [blockId]: newId });
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

      {/* Cluster cards */}
      <div className="space-y-2">
        {clusters.map((c) => {
          const status = highestStatus(c);
          const previewC = previewByClusterId[c.cluster_id];
          const previewStatus = previewC ? highestStatus(previewC) : null;
          const previewing = !!previewC && previewStatus !== status;
          const display = previewC ?? c;
          const dispStatus = previewStatus ?? status;
          const label = STATUS_LABEL[dispStatus];
          return (
            <div
              key={c.cluster_id}
              onDragOver={handleDragOver(c.cluster_id)}
              onDragLeave={handleDragLeave(c.cluster_id)}
              onDrop={handleDrop(c.cluster_id)}
              className={`rounded-md border-2 p-3 transition-colors ${
                hoverClusterId === c.cluster_id
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
                    {display.total_area_ha} ha · {display.block_names.length} block
                    {display.block_names.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${label.pillClass}`}
                  title={label.detail}
                >
                  {previewing && "→ "}
                  {label.pill}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{label.detail}</p>

              {/* Block chips inside this cluster */}
              <div className="mt-2 flex flex-wrap gap-2">
                {display.block_ids.map((bid, idx) => {
                  const blockName = display.block_names[idx];
                  const blockMeta = blocks.find((b) => b.block_id === bid);
                  const isPreview = previewC && !c.block_ids.includes(bid);
                  return (
                    <BlockChip
                      key={bid}
                      blockName={blockName}
                      area={blockMeta?.block_area_ha ?? null}
                      onDragStart={handleDragStart(bid)}
                      onDragEnd={handleDragEnd}
                      ghostPreview={isPreview}
                    />
                  );
                })}
              </div>

              {/* Per-nutrient warnings */}
              {display.heterogeneity.warnings.length > 0 && (
                <ul className="mt-2 space-y-0.5 text-xs">
                  {display.heterogeneity.warnings.map((w) => (
                    <WarningLine key={w.nutrient} warning={w} />
                  ))}
                </ul>
              )}

              {previewing && previewStatus === "split" && status !== "split" && (
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

      <p className="mt-3 text-[11px] text-muted-foreground">
        Heterogeneity thresholds: Wilding (1985) via Mulla &amp; Schepers (1997).
      </p>
    </div>
  );
}

interface BlockChipProps {
  blockName: string;
  area: number | null;
  dataless?: boolean;
  ghostPreview?: boolean;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
}

function BlockChip({ blockName, area, dataless, ghostPreview, onDragStart, onDragEnd }: BlockChipProps) {
  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={`inline-flex cursor-grab items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs select-none active:cursor-grabbing ${
        ghostPreview
          ? "border-dashed border-[var(--sapling-orange)] bg-orange-50/50 text-[var(--sapling-orange)]"
          : dataless
            ? "border-amber-300 bg-amber-100/60 text-amber-900"
            : "border-gray-200 bg-white text-[var(--sapling-dark)]"
      }`}
      title={
        dataless
          ? "No soil analysis — drag onto a recipe to apply a rough plan."
          : "Drag to reassign"
      }
    >
      <span className="font-medium">{blockName}</span>
      {area != null && (
        <span className="text-[10px] text-muted-foreground">{area} ha</span>
      )}
      {dataless && (
        <span className="text-[10px] uppercase tracking-wide text-amber-700">no soil</span>
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
