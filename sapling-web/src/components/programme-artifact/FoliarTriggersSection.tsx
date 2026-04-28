"use client";

/**
 * Foliar events grouped by trigger reasoning. Each group header
 * explains *why* the engine fired this kind of foliar (peak demand,
 * soil gap, leaf correction, etc.) and the events under it carry the
 * concrete who/when/what.
 *
 * Rendered last in the artifact view so the scaffold reads as: soil
 * → group programmes → foliar contingencies. Foliar is reactive
 * supplement, not a primary driver, so it lives at the bottom.
 */

import type { FoliarEvent } from "@/lib/types/programme-artifact";
import { Leaf } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const TRIGGER_HEADLINE: Record<string, string> = {
  soil_availability_gap: "Soil-availability gaps",
  stage_peak_demand: "Stage peak demand",
  quality_window: "Quality / fruit-set window",
  leaf_correction: "Leaf-analysis correction",
  cultivar_specific: "Cultivar-specific protocol",
};

const TRIGGER_RATIONALE: Record<string, string> = {
  soil_availability_gap:
    "Soil supply is below crop demand for the listed nutrient(s); foliar bridges the gap during peak uptake.",
  stage_peak_demand:
    "Demand spikes faster than soil delivery during this growth stage; foliar matches the curve.",
  quality_window:
    "Crucial fruit-set or quality window — direct-leaf delivery beats relying on root uptake.",
  leaf_correction:
    "Leaf analysis flagged a deficiency; foliar applied as a corrective.",
  cultivar_specific:
    "Cultivar-specific protocol from FERTASA/SAMAC/SASRI/CRI — recurring practice.",
};

const TRIGGER_ICON_BG: Record<string, string> = {
  soil_availability_gap: "bg-amber-100 text-amber-800",
  stage_peak_demand: "bg-emerald-100 text-emerald-800",
  quality_window: "bg-purple-100 text-purple-800",
  leaf_correction: "bg-rose-100 text-rose-800",
  cultivar_specific: "bg-sky-100 text-sky-800",
};

function formatSprayDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-ZA", {
    day: "numeric",
    month: "short",
  });
}

interface Props {
  events: FoliarEvent[];
  blockNameById: Record<string, string>;
}

export function FoliarTriggersSection({ events, blockNameById }: Props) {
  if (!events || events.length === 0) return null;

  // Group by trigger_kind. The engine emits one event per (block, week,
  // trigger), so the same trigger fires across blocks and weeks — the
  // group header is a single rationale, the rows are the schedule.
  const byTrigger = new Map<string, FoliarEvent[]>();
  for (const e of events) {
    const key = e.trigger_kind || "stage_peak_demand";
    if (!byTrigger.has(key)) byTrigger.set(key, []);
    byTrigger.get(key)!.push(e);
  }
  // Stable order — soil gaps and leaf corrections first (corrective);
  // peak demand and quality window after (anticipatory); cultivar-
  // specific last (informational).
  const ORDER = [
    "leaf_correction",
    "soil_availability_gap",
    "stage_peak_demand",
    "quality_window",
    "cultivar_specific",
  ];
  const groups = [...byTrigger.entries()].sort(
    (a, b) => (ORDER.indexOf(a[0]) === -1 ? 99 : ORDER.indexOf(a[0])) -
      (ORDER.indexOf(b[0]) === -1 ? 99 : ORDER.indexOf(b[0])),
  );

  return (
    <section className="space-y-3">
      <header className="flex items-center gap-2">
        <Leaf className="size-4 text-[var(--sapling-orange)]" />
        <h2 className="text-sm font-semibold uppercase tracking-wide">
          Foliar events · {events.length} spray{events.length !== 1 ? "s" : ""}
        </h2>
      </header>
      <div className="space-y-3">
        {groups.map(([kind, list]) => {
          const headline = TRIGGER_HEADLINE[kind] ?? kind;
          const rationale = TRIGGER_RATIONALE[kind] ?? "";
          const pillCls = TRIGGER_ICON_BG[kind] ?? "bg-muted text-muted-foreground";
          // Sort within a trigger group: by spray_date ascending, then
          // by block name for stable display order.
          list.sort((a, b) => {
            if (a.spray_date !== b.spray_date) {
              return a.spray_date < b.spray_date ? -1 : 1;
            }
            return (a.block_id || "").localeCompare(b.block_id || "");
          });
          return (
            <Card key={kind}>
              <CardContent className="p-5">
                <div className="mb-3 flex flex-wrap items-baseline gap-3 border-b pb-2">
                  <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ${pillCls}`}>
                    {headline}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {list.length} event{list.length !== 1 ? "s" : ""}
                  </span>
                </div>
                {rationale && (
                  <p className="mb-3 text-xs italic leading-snug text-muted-foreground">
                    {rationale}
                  </p>
                )}
                <ul className="divide-y divide-border/30">
                  {list.map((e, i) => (
                    <li key={`${e.block_id}-${e.spray_date}-${i}`} className="py-2.5">
                      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                        <span className="text-sm font-medium text-foreground">
                          {e.product}
                        </span>
                        <span className="font-mono text-xs text-muted-foreground">
                          {e.analysis}
                        </span>
                        <span className="ml-auto text-xs text-foreground">
                          {formatSprayDate(e.spray_date)}
                        </span>
                      </div>
                      <p className="mt-0.5 text-[11px] text-muted-foreground">
                        {blockNameById[e.block_id] ?? e.block_id} · {e.stage_name}
                        {e.rate_per_ha && ` · ${e.rate_per_ha}`}
                      </p>
                      {e.trigger_reason && (
                        <p className="mt-0.5 text-[11px] italic text-muted-foreground/80">
                          {e.trigger_reason}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
