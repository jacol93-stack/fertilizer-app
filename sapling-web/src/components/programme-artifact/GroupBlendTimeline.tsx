"use client";

/**
 * Per-group fertilizer programme timeline.
 *
 * Groups (clusters of blocks sharing one programme) are listed A → B →
 * C, and each group's blends are numbered A1, A2, A3, … in season
 * order. Each application row carries: code · stage · month/date ·
 * method · nutrients delivered (kg/ha) · 1-line "why this blend"
 * brief. Raw materials are NEVER shown — that crosses the client-
 * disclosure boundary (Act 36 / proprietary blends).
 */

import type {
  Blend,
  SoilSnapshot,
} from "@/lib/types/programme-artifact";
import { Droplets } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { methodLabel } from "@/lib/season-constants";

interface GroupBlendTimelineProps {
  blends: Blend[];
  snapshots: SoilSnapshot[];
}

interface GroupRow {
  letter: string;
  source_block_id: string; // raw id from the artifact (cluster_A or block id)
  display_name: string; // "Group A — 35 ha · 2 blocks"
  blocks: string[]; // block names making up the group
  total_area_ha: number;
  blends: Array<Blend & { code: string }>;
}

const NUTRIENT_LABEL: Record<string, string> = {
  N: "N", P2O5: "P₂O₅", K2O: "K₂O",
  Ca: "Ca", Mg: "Mg", S: "S",
  Zn: "Zn", B: "B", Mn: "Mn", Fe: "Fe", Cu: "Cu", Mo: "Mo",
};

const NUTRIENT_ORDER = ["N", "P2O5", "K2O", "Ca", "Mg", "S", "Zn", "B", "Mn", "Fe", "Cu", "Mo"];

function fmtNumber(n: number, dp = 1): string {
  if (n === 0) return "0";
  if (Math.abs(n) >= 100) return n.toFixed(0);
  if (Math.abs(n) >= 10) return n.toFixed(0);
  return n.toFixed(dp);
}

/** "cluster_A" → "A", or fallback to first letter of block name. */
function letterFromBlockId(blockId: string, fallbackIdx: number): string {
  const m = blockId.match(/^cluster_([A-Z])/i);
  if (m) return m[1].toUpperCase();
  return String.fromCharCode("A".charCodeAt(0) + fallbackIdx);
}

function compareDate(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

function buildGroupRows(
  blends: Blend[],
  snapshots: SoilSnapshot[],
): GroupRow[] {
  // One bucket per source block_id from the artifact (cluster_A or a
  // singleton block id). Blends for the same group share a block_id.
  const byId = new Map<string, Blend[]>();
  for (const b of blends) {
    if (!byId.has(b.block_id)) byId.set(b.block_id, []);
    byId.get(b.block_id)!.push(b);
  }

  // Lookup table: source id → snapshot for headline context.
  const snapshotById = new Map<string, SoilSnapshot>();
  for (const s of snapshots) snapshotById.set(s.block_id, s);

  // Groups from cluster_X go in alphabetical letter order; singleton
  // (non-cluster) groups follow, also stably ordered.
  const clusterIds = [...byId.keys()].filter((id) => id.startsWith("cluster_")).sort();
  const singletonIds = [...byId.keys()].filter((id) => !id.startsWith("cluster_")).sort();
  const orderedIds = [...clusterIds, ...singletonIds];

  const rows: GroupRow[] = orderedIds.map((id, idx) => {
    const blendList = byId.get(id) ?? [];
    // Order blends by first event date (or stage_number as fallback for
    // legacy artifacts without applications). Establishes A1, A2, A3 …
    blendList.sort((a, b) => {
      const aFirst = a.applications?.[0]?.event_date ?? "";
      const bFirst = b.applications?.[0]?.event_date ?? "";
      if (aFirst && bFirst) return compareDate(aFirst, bFirst);
      return a.stage_number - b.stage_number;
    });
    const letter = letterFromBlockId(id, idx);
    const snap = snapshotById.get(id);
    // For multi-block clusters the snapshot's block_name carries the
    // member list; for singletons it's just the block name.
    const blocks = snap
      ? snap.block_name.includes(",")
        ? snap.block_name.split(",").map((s) => s.trim())
        : [snap.block_name]
      : [];
    return {
      letter,
      source_block_id: id,
      display_name: snap ? snap.block_name : id,
      blocks,
      total_area_ha: snap?.block_area_ha ?? 0,
      blends: blendList.map((b, i) => ({ ...b, code: `${letter}${i + 1}` })),
    };
  });

  return rows;
}

/** Synthesize a 1-line "why this blend" brief from stage purpose,
 * dominant nutrient(s) delivered, and method — no raw-material names. */
function brief(b: Blend, snap?: SoilSnapshot): string {
  const nutrients = Object.entries(b.nutrients_delivered)
    .filter(([, v]) => v > 0)
    .sort((a, c) => c[1] - a[1]);
  const top = nutrients.slice(0, 2).map(([k]) => NUTRIENT_LABEL[k] ?? k);
  const stage = b.stage_name || `Stage ${b.stage_number}`;
  const method = methodLabel(b.method.kind).toLowerCase();
  const events = b.events ?? b.applications?.length ?? 1;
  const eventsClause = events > 1 ? ` Split into ${events} events.` : "";

  // Tie back to soil context where there's a relevant signal.
  let soilTie = "";
  if (snap?.factor_findings && top.length > 0) {
    const linked = snap.factor_findings.find((f) =>
      f.severity !== "info" &&
      top.some((t) => f.parameter.toUpperCase().includes(t.replace(/[^A-Z]/g, ""))),
    );
    if (linked) {
      soilTie = ` Sized to address ${linked.parameter} (${linked.severity}).`;
    }
  }

  if (top.length === 0) {
    return `${stage} — applied via ${method}.${eventsClause}${soilTie}`;
  }
  if (top.length === 1) {
    return `${stage} window targets ${top[0]} demand; applied via ${method}.${eventsClause}${soilTie}`;
  }
  return `${stage} window targets ${top.join(" + ")} demand; applied via ${method}.${eventsClause}${soilTie}`;
}

function NutrientChips({ blend }: { blend: Blend }) {
  const entries = NUTRIENT_ORDER
    .map((k) => [k, blend.nutrients_delivered[k]] as const)
    .filter(([, v]) => v && v > 0);
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {entries.map(([k, v]) => (
        <span
          key={k}
          className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] tabular-nums"
        >
          <span className="font-semibold">{NUTRIENT_LABEL[k] ?? k}</span>
          <span className="ml-1">{fmtNumber(v)}</span>
        </span>
      ))}
    </div>
  );
}

function BlendRow({ blend, snap }: { blend: Blend & { code: string }; snap?: SoilSnapshot }) {
  const events = blend.events ?? blend.applications?.length ?? 1;
  const dateLabel = blend.dates_label || blend.weeks || "";
  return (
    <li className="grid grid-cols-[auto_1fr] items-start gap-3 border-b border-border/40 py-3 last:border-0">
      <span className="rounded-md bg-[var(--sapling-orange)] px-2 py-1 text-xs font-bold text-white">
        {blend.code}
      </span>
      <div className="min-w-0 space-y-1.5">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
          <span className="text-sm font-semibold text-foreground">
            {blend.stage_name || `Stage ${blend.stage_number}`}
          </span>
          <span className="text-xs text-muted-foreground">
            {dateLabel}
            {events > 1 && ` · ${events} events`}
          </span>
          <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            {methodLabel(blend.method.kind)}
          </span>
        </div>
        <NutrientChips blend={blend} />
        <p className="text-[11px] leading-snug text-muted-foreground">
          {brief(blend, snap)}
        </p>
      </div>
    </li>
  );
}

export function GroupBlendTimeline({
  blends,
  snapshots,
}: GroupBlendTimelineProps) {
  if (!blends || blends.length === 0) return null;
  const groups = buildGroupRows(blends, snapshots);
  const snapshotById = new Map(snapshots.map((s) => [s.block_id, s]));
  if (groups.every((g) => g.blends.length === 0)) return null;

  return (
    <section className="space-y-3">
      <header className="flex items-center gap-2">
        <Droplets className="size-4 text-[var(--sapling-orange)]" />
        <h2 className="text-sm font-semibold uppercase tracking-wide">
          Programme · {groups.length} group{groups.length !== 1 ? "s" : ""}
        </h2>
      </header>
      <div className="space-y-3">
        {groups.map((g) => (
          <Card key={g.source_block_id}>
            <CardContent className="p-5">
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b pb-2">
                <div className="flex items-baseline gap-3">
                  <span className="flex size-9 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-base font-bold text-white">
                    {g.letter}
                  </span>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">
                      Group {g.letter}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {g.total_area_ha > 0 && `${g.total_area_ha} ha · `}
                      {g.blocks.length} block{g.blocks.length !== 1 ? "s" : ""}
                      {g.blocks.length > 0 && ` · ${g.blocks.join(", ")}`}
                    </p>
                  </div>
                </div>
                <span className="rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                  {g.blends.length} application{g.blends.length !== 1 ? "s" : ""}
                </span>
              </div>
              <ul className="divide-y divide-transparent">
                {g.blends.map((b) => (
                  <BlendRow
                    key={b.code}
                    blend={b}
                    snap={snapshotById.get(g.source_block_id)}
                  />
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
