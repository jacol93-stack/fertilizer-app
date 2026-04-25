"use client";

import type {
  Assumption,
  Blend,
  Concentrate,
  FoliarEvent,
  OutstandingItem,
  PreSeasonInput,
  PreSeasonRecommendation,
  ProgrammeArtifact,
  RiskFlag,
  Severity,
  ShoppingListEntry,
  SoilSnapshot,
  SourceCitation,
  StageSchedule,
} from "@/lib/types/programme-artifact";
import { TIER_LABEL, Tier } from "@/lib/types/programme-artifact";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Droplets,
  FlaskConical,
  Info,
  Leaf,
  ListChecks,
  Package,
  Shovel,
  Sprout,
} from "lucide-react";
import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

// ============================================================
// Main container
// ============================================================

/**
 * Build a block_id → display-name map from the artifact's soil
 * snapshots so downstream sections can render human labels instead of
 * raw IDs (especially useful under Phase 3 clustering, where
 * block_id can be e.g. "cluster_A"). Multi-block clusters have both a
 * cluster-level snapshot and per-original-block snapshots; we prefer
 * whichever entry's block_id exactly matches the lookup, so the
 * labels come out right in both layers.
 */
function buildBlockNameMap(snapshots: SoilSnapshot[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const s of snapshots) {
    if (!out[s.block_id]) out[s.block_id] = s.block_name;
  }
  return out;
}

function formatEventDate(iso: string): string {
  // Parse as local date (avoid UTC shift); backend sends "YYYY-MM-DD".
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-ZA", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function prettyBlockLabel(
  blockId: string,
  nameById: Record<string, string>,
): string {
  const name = nameById[blockId];
  if (name) return name;
  // Fallback when blends reference an id that's not in the snapshots
  // (shouldn't happen but defensive). Cluster-ID prettifying:
  if (blockId.startsWith("cluster_")) {
    return `Cluster ${blockId.slice("cluster_".length)}`;
  }
  return `Block ${blockId}`;
}

export function ArtifactView({ artifact }: { artifact: ProgrammeArtifact }) {
  const blockNameById = buildBlockNameMap(artifact.soil_snapshots);
  return (
    <div className="space-y-6">
      <HeaderCard artifact={artifact} />
      <SoilSnapshotsSection snapshots={artifact.soil_snapshots} />
      <PreSeasonSection
        inputs={artifact.pre_season_inputs}
        recommendations={artifact.pre_season_recommendations}
      />
      <StageScheduleSection
        schedules={artifact.stage_schedules}
        blockNameById={blockNameById}
      />
      <BlendsSection
        blends={artifact.blends}
        blockNameById={blockNameById}
      />
      <FoliarSection events={artifact.foliar_events} />
      <ShoppingListSection
        entries={artifact.shopping_list}
        blockNameById={blockNameById}
      />
      <RiskFlagsSection flags={artifact.risk_flags} />
      <OutstandingItemsSection items={artifact.outstanding_items} />
      <AssumptionsSection assumptions={artifact.assumptions} />
      <SourcesAuditSection sources={artifact.sources_audit} />
      <DecisionTraceSection trace={artifact.decision_trace} />
    </div>
  );
}

// ============================================================
// Header
// ============================================================

function HeaderCard({ artifact }: { artifact: ProgrammeArtifact }) {
  const h = artifact.header;
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {h.crop} — {h.farm_name}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {h.client_name} · {h.location || "—"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Prepared for {h.prepared_for} by {h.prepared_by} · {h.prepared_date}
              {h.ref_number && <> · Ref {h.ref_number}</>}
            </p>
          </div>
          <StateBadge state={h.state} />
        </div>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
          <Stat label="Planting" value={h.planting_date} />
          <Stat
            label="Harvest"
            value={h.expected_harvest_date || "—"}
          />
          <Stat label="Season" value={h.season || "—"} />
          <Stat
            label="Data confidence"
            value={h.data_completeness.level}
          />
          <Stat
            label="Blocks"
            value={String(artifact.soil_snapshots.length)}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function StateBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    draft: "bg-muted text-muted-foreground",
    approved: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100",
    activated: "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100",
    in_progress: "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-100",
    completed: "bg-purple-100 text-purple-900 dark:bg-purple-900/40 dark:text-purple-100",
    archived: "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
  };
  return (
    <span
      className={`px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wide ${
        colors[state] || colors.draft
      }`}
    >
      {state}
    </span>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground uppercase tracking-wide">
        {label}
      </div>
      <div className="mt-0.5 font-medium">{value}</div>
    </div>
  );
}

// ============================================================
// Soil Snapshots
// ============================================================

function SoilSnapshotsSection({ snapshots }: { snapshots: SoilSnapshot[] }) {
  if (snapshots.length === 0) return null;
  return (
    <Section icon={<FlaskConical className="h-4 w-4" />} title="Soil analysis">
      <div className="space-y-4">
        {snapshots.map((s) => (
          <div key={s.block_id} className="border border-border rounded-md p-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h3 className="font-medium">{s.block_name}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {s.block_area_ha} ha · {s.lab_name || "Lab n/a"}
                  {s.lab_method && <> · {s.lab_method}</>}
                  {s.sample_date && <> · sampled {s.sample_date}</>}
                </p>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-x-4 gap-y-2 text-sm">
              {Object.entries(s.parameters).map(([k, v]) => (
                <div key={k}>
                  <span className="text-xs text-muted-foreground">{k}</span>
                  <div className="font-mono">{v}</div>
                </div>
              ))}
            </div>
            {s.headline_signals.length > 0 && (
              <div className="mt-3 space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Headline signals
                </div>
                <ul className="list-disc list-inside text-sm space-y-0.5">
                  {s.headline_signals.map((sig, i) => (
                    <li key={i}>{sig}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

// ============================================================
// Pre-Season
// ============================================================

function PreSeasonSection({
  inputs,
  recommendations,
}: {
  inputs: PreSeasonInput[];
  recommendations: PreSeasonRecommendation[];
}) {
  if (inputs.length === 0 && recommendations.length === 0) return null;
  return (
    <Section icon={<Shovel className="h-4 w-4" />} title="Pre-season">
      {inputs.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium mb-2">Already applied</h3>
          <div className="space-y-2">
            {inputs.map((p, i) => (
              <div
                key={i}
                className="border border-border rounded-md p-3 text-sm"
              >
                <div className="flex justify-between gap-4">
                  <div>
                    <span className="font-medium">{p.product}</span>
                    <span className="text-muted-foreground"> · {p.rate}</span>
                  </div>
                  {p.applied_date && (
                    <span className="text-xs text-muted-foreground">
                      {p.applied_date}
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {p.status_at_planting}
                </div>
                {(p.effective_n_kg_per_ha > 0 ||
                  p.effective_p2o5_kg_per_ha > 0 ||
                  p.effective_ca_kg_per_ha > 0 ||
                  p.effective_s_kg_per_ha > 0) && (
                  <div className="mt-2 text-xs font-mono text-muted-foreground">
                    Effective at planting:
                    {p.effective_n_kg_per_ha > 0 &&
                      ` N ${p.effective_n_kg_per_ha}`}
                    {p.effective_p2o5_kg_per_ha > 0 &&
                      ` · P₂O₅ ${p.effective_p2o5_kg_per_ha}`}
                    {p.effective_k2o_kg_per_ha > 0 &&
                      ` · K₂O ${p.effective_k2o_kg_per_ha}`}
                    {p.effective_ca_kg_per_ha > 0 &&
                      ` · Ca ${p.effective_ca_kg_per_ha}`}
                    {p.effective_mg_kg_per_ha > 0 &&
                      ` · Mg ${p.effective_mg_kg_per_ha}`}
                    {p.effective_s_kg_per_ha > 0 &&
                      ` · S ${p.effective_s_kg_per_ha}`}{" "}
                    kg/ha
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {recommendations.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2">Recommended actions</h3>
          <div className="space-y-2">
            {recommendations.map((r, i) => (
              <div
                key={i}
                className="border-l-4 border-primary pl-3 py-1 text-sm space-y-1"
              >
                <div className="font-medium">
                  {r.material} · {r.target_rate_per_ha}
                </div>
                <div className="text-xs text-muted-foreground">
                  Apply by <span className="font-mono">{r.recommended_apply_by_date}</span>{" "}
                  (reaction time {r.reaction_time_months} months)
                </div>
                <div className="text-xs">
                  <span className="font-medium">Why:</span> {r.reason}
                </div>
                <div className="text-xs text-muted-foreground">{r.purpose}</div>
                <div className="text-xs text-muted-foreground italic">
                  {r.expected_status_at_planting}
                </div>
                <SourceTag source={r.source} />
              </div>
            ))}
          </div>
        </div>
      )}
    </Section>
  );
}

// ============================================================
// Stage Schedule
// ============================================================

function StageScheduleSection({
  schedules,
  blockNameById,
}: {
  schedules: StageSchedule[];
  blockNameById: Record<string, string>;
}) {
  if (schedules.length === 0) return null;
  return (
    <Section icon={<Sprout className="h-4 w-4" />} title="Stage schedule">
      <div className="space-y-4">
        {schedules.map((sch) => (
          <div key={sch.block_id}>
            <h3 className="text-sm font-medium mb-2">
              {prettyBlockLabel(sch.block_id, blockNameById)}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted-foreground uppercase tracking-wide text-left border-b border-border">
                    <th className="py-2 pr-3">Stage</th>
                    <th className="py-2 pr-3">Weeks</th>
                    <th className="py-2 pr-3">Dates</th>
                    <th className="py-2 pr-3">Events</th>
                  </tr>
                </thead>
                <tbody>
                  {sch.stages.map((stg) => (
                    <tr
                      key={stg.stage_number}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="py-2 pr-3">
                        <span className="font-medium">{stg.stage_number}.</span>{" "}
                        {stg.stage_name}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs">
                        {stg.week_start}–{stg.week_end}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs">
                        {stg.date_start} → {stg.date_end}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs">
                        {stg.events}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ============================================================
// Blends
// ============================================================

function BlendsSection({
  blends,
  blockNameById,
}: {
  blends: Blend[];
  blockNameById: Record<string, string>;
}) {
  if (blends.length === 0) {
    return (
      <Section icon={<Droplets className="h-4 w-4" />} title="Blends">
        <p className="text-sm text-muted-foreground italic">
          No blends produced — materials catalog may not have been provided or
          no method assignments required blending.
        </p>
      </Section>
    );
  }
  // Group by block
  const byBlock = new Map<string, Blend[]>();
  for (const b of blends) {
    const arr = byBlock.get(b.block_id) || [];
    arr.push(b);
    byBlock.set(b.block_id, arr);
  }
  return (
    <Section icon={<Droplets className="h-4 w-4" />} title="Blends">
      <div className="space-y-4">
        {[...byBlock.entries()].map(([blockId, blockBlends]) => (
          <div key={blockId}>
            <h3 className="text-sm font-medium mb-2">
              {prettyBlockLabel(blockId, blockNameById)}
            </h3>
            <div className="space-y-3">
              {blockBlends.map((b, i) => (
                <BlendCard key={i} blend={b} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

function BlendCard({ blend }: { blend: Blend }) {
  const isLiquid = blend.method.kind.startsWith("liquid_");
  // Defensive: legacy artifacts (built before F3) have no `applications`
  // field on blends. Treat missing/empty as a single-event blend.
  const applications = blend.applications ?? [];
  const eventCount = blend.events ?? applications.length ?? 1;
  return (
    <div className="border border-border rounded-md p-4 space-y-3">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h4 className="font-medium">
            Blend {blend.stage_number}: {blend.stage_name}
          </h4>
          <p className="text-xs text-muted-foreground">
            {blend.weeks} · {blend.dates_label} · {eventCount} event
            {eventCount > 1 ? "s" : ""} · {blend.method.kind}
          </p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-muted-foreground uppercase tracking-wide text-left border-b border-border">
              <th className="py-2 pr-3">Product</th>
              <th className="py-2 pr-3">Analysis</th>
              {isLiquid && <th className="py-2 pr-3">Stream</th>}
              <th className="py-2 pr-3">Per event /ha</th>
              <th className="py-2 pr-3">Per stage /ha</th>
              <th className="py-2 pr-3">Batch total</th>
            </tr>
          </thead>
          <tbody>
            {blend.raw_products.map((p, i) => (
              <tr
                key={i}
                className="border-b border-border/50 last:border-0"
              >
                <td className="py-2 pr-3 font-medium">{p.product}</td>
                <td className="py-2 pr-3 text-xs">{p.analysis}</td>
                {isLiquid && (
                  <td className="py-2 pr-3 text-xs font-mono">
                    {p.stream ? `Part ${p.stream}` : "—"}
                  </td>
                )}
                <td className="py-2 pr-3 font-mono text-xs">
                  {p.rate_per_event_per_ha || "—"}
                </td>
                <td className="py-2 pr-3 font-mono text-xs">
                  {p.rate_per_stage_per_ha || "—"}
                </td>
                <td className="py-2 pr-3 font-mono text-xs">
                  {p.batch_total || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {applications.length > 1 && (
        <div className="pt-2 border-t border-border/50 space-y-2">
          <h5 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Application schedule
          </h5>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-xs text-muted-foreground uppercase tracking-wide text-left border-b border-border">
                  <th className="py-1.5 pr-3">#</th>
                  <th className="py-1.5 pr-3">Date</th>
                  <th className="py-1.5 pr-3 text-right">Week</th>
                  <th className="py-1.5 pr-3">Of stage</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app, i) => (
                  <tr
                    key={app.event_index}
                    className="border-b border-border/30 last:border-0"
                  >
                    <td className="py-1.5 pr-3 font-mono">{i + 1}</td>
                    <td className="py-1.5 pr-3">{formatEventDate(app.event_date)}</td>
                    <td className="py-1.5 pr-3 font-mono text-right">{app.week_from_planting}</td>
                    <td className="py-1.5 pr-3 font-mono text-muted-foreground">
                      {i + 1} of {applications.length}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {blend.concentrates.length > 0 && (
        <div className="pt-2 border-t border-border/50 space-y-2">
          <h5 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Concentrates to manufacture
          </h5>
          {blend.concentrates.map((c, i) => (
            <ConcentrateCard key={i} concentrate={c} />
          ))}
        </div>
      )}
      {Object.keys(blend.nutrients_delivered).length > 0 && (
        <div className="pt-2 border-t border-border/50 text-xs">
          <span className="font-medium">Stage delivers per ha:</span>{" "}
          {Object.entries(blend.nutrients_delivered)
            .filter(([, v]) => v > 0)
            .map(([k, v]) => `${k} ${v}`)
            .join(" · ") || "—"}{" "}
          kg/ha
        </div>
      )}
    </div>
  );
}

function ConcentrateCard({ concentrate }: { concentrate: Concentrate }) {
  return (
    <div className="bg-muted/30 rounded p-3 text-sm space-y-1">
      <div className="font-medium">{concentrate.name}</div>
      <div className="text-xs text-muted-foreground">
        Contains: {concentrate.contains}
      </div>
      <div className="text-xs font-mono">
        {concentrate.dry_weight_or_liquid}
        {concentrate.strength_g_per_l && (
          <> · {concentrate.strength_g_per_l} g/L</>
        )}
        {concentrate.volume_l && <> · {concentrate.volume_l} L</>}
      </div>
      {concentrate.injection_notes && (
        <div className="text-xs text-muted-foreground italic">
          {concentrate.injection_notes}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Foliar Events
// ============================================================

function FoliarSection({ events }: { events: FoliarEvent[] }) {
  if (events.length === 0) return null;
  return (
    <Section icon={<Leaf className="h-4 w-4" />} title="Foliar spray events">
      <div className="space-y-2">
        {events.map((e, i) => (
          <div
            key={i}
            className="border-l-4 border-green-500 pl-3 py-2 space-y-1 text-sm"
          >
            <div className="flex items-baseline justify-between gap-4 flex-wrap">
              <div className="font-medium">
                #{e.event_number}: {e.product} · {e.rate_per_ha}
              </div>
              <div className="text-xs text-muted-foreground font-mono">
                Wk {e.week} · {e.spray_date}
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              {e.stage_name} · {e.analysis} · total {e.total_for_block}
            </div>
            <div className="text-xs">
              <span className="font-medium">Trigger ({e.trigger_kind}):</span>{" "}
              {e.trigger_reason}
            </div>
            <SourceTag source={e.source} />
          </div>
        ))}
      </div>
    </Section>
  );
}

// ============================================================
// Shopping List
// ============================================================

const CATEGORY_LABEL: Record<string, string> = {
  drip: "Fertigation / drip",
  drench: "Drench",
  foliar: "Foliar",
  dry_blend: "Dry blend / broadcast",
};

function ShoppingListSection({
  entries,
  blockNameById,
}: {
  entries: ShoppingListEntry[];
  blockNameById: Record<string, string>;
}) {
  if (entries.length === 0) return null;
  // Group by category and sort within each
  const byCategory = new Map<string, ShoppingListEntry[]>();
  for (const e of entries) {
    const arr = byCategory.get(e.category) || [];
    arr.push(e);
    byCategory.set(e.category, arr);
  }
  const categories = Array.from(byCategory.keys()).sort();

  return (
    <Section icon={<Package className="h-4 w-4" />} title="Shopping list">
      <div className="space-y-5">
        {categories.map((cat) => {
          const rows = byCategory.get(cat) || [];
          const rowsSorted = [...rows].sort((a, b) => b.total_overall - a.total_overall);
          const catTotal = rowsSorted.reduce((s, r) => s + r.total_overall, 0);
          return (
            <div key={cat}>
              <div className="mb-2 flex items-baseline justify-between gap-3">
                <h3 className="text-sm font-medium">
                  {CATEGORY_LABEL[cat] || cat}
                </h3>
                <span className="text-xs text-muted-foreground">
                  {rowsSorted.length} product{rowsSorted.length !== 1 ? "s" : ""}
                  {rowsSorted[0]?.unit ? ` · ${catTotal.toFixed(0)} ${rowsSorted[0].unit} total` : ""}
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="py-2 pr-3">Product</th>
                      <th className="py-2 pr-3">Analysis</th>
                      <th className="py-2 pr-3 text-right">Total</th>
                      <th className="py-2 pr-3">Per block</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rowsSorted.map((r, i) => (
                      <tr key={i} className="border-b border-border/50 last:border-0 align-top">
                        <td className="py-2 pr-3 font-medium">{r.product}</td>
                        <td className="py-2 pr-3 text-xs">{r.analysis}</td>
                        <td className="py-2 pr-3 text-right font-mono text-xs tabular-nums">
                          {r.total_overall.toFixed(0)} {r.unit}
                        </td>
                        <td className="py-2 pr-3 text-xs">
                          {Object.entries(r.total_per_block)
                            .map(([bid, q]) => `${prettyBlockLabel(bid, blockNameById)}: ${q.toFixed(0)} ${r.unit}`)
                            .join(" · ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

// ============================================================
// Risk Flags
// ============================================================

function RiskFlagsSection({ flags }: { flags: RiskFlag[] }) {
  if (flags.length === 0) return null;
  // Sort by severity
  const order: Record<Severity, number> = {
    critical: 0,
    warn: 1,
    watch: 2,
    info: 3,
  };
  const sorted = [...flags].sort(
    (a, b) => (order[a.severity] ?? 4) - (order[b.severity] ?? 4),
  );
  return (
    <Section icon={<AlertTriangle className="h-4 w-4" />} title="Risk flags">
      <div className="space-y-2">
        {sorted.map((f, i) => (
          <RiskFlagItem key={i} flag={f} />
        ))}
      </div>
    </Section>
  );
}

function RiskFlagItem({ flag }: { flag: RiskFlag }) {
  const colors: Record<Severity, string> = {
    critical: "border-red-500 bg-red-50 dark:bg-red-950/20",
    warn: "border-orange-500 bg-orange-50 dark:bg-orange-950/20",
    watch: "border-amber-500 bg-amber-50 dark:bg-amber-950/20",
    info: "border-blue-500 bg-blue-50 dark:bg-blue-950/20",
  };
  return (
    <div
      className={`border-l-4 pl-3 py-2 ${colors[flag.severity] || colors.info}`}
    >
      <div className="flex items-start gap-2">
        <SeverityIcon severity={flag.severity} />
        <div className="flex-1 text-sm">
          <div className="text-xs font-medium uppercase tracking-wide opacity-70">
            {flag.severity}
          </div>
          <div className="mt-0.5">{flag.message}</div>
          {flag.source && (
            <div className="mt-1">
              <SourceTag source={flag.source} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SeverityIcon({ severity }: { severity: Severity }) {
  if (severity === "critical") return <CircleAlert className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />;
  if (severity === "warn") return <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 shrink-0" />;
  if (severity === "watch") return <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />;
  return <Info className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />;
}

// ============================================================
// Outstanding Items
// ============================================================

function OutstandingItemsSection({ items }: { items: OutstandingItem[] }) {
  if (items.length === 0) return null;
  return (
    <Section
      icon={<ListChecks className="h-4 w-4" />}
      title="Outstanding items"
    >
      <ul className="space-y-3">
        {items.map((it, i) => (
          <li key={i} className="text-sm space-y-1">
            <div className="font-medium">{it.item}</div>
            <div className="text-xs text-muted-foreground">
              {it.why_it_matters}
            </div>
            {it.impact_if_skipped && (
              <div className="text-xs text-red-700 dark:text-red-300">
                Impact if skipped: {it.impact_if_skipped}
              </div>
            )}
          </li>
        ))}
      </ul>
    </Section>
  );
}

// ============================================================
// Assumptions
// ============================================================

function AssumptionsSection({ assumptions }: { assumptions: Assumption[] }) {
  if (assumptions.length === 0) return null;
  return (
    <Collapsible
      icon={<Info className="h-4 w-4" />}
      title={`Assumptions (${assumptions.length})`}
      defaultOpen={false}
    >
      <div className="space-y-2">
        {assumptions.map((a, i) => (
          <div key={i} className="text-sm border-l-2 border-muted pl-3 py-1">
            <div className="font-medium">
              {a.field}:{" "}
              <span className="font-normal">{a.assumed_value}</span>
            </div>
            {a.override_guidance && (
              <div className="text-xs text-muted-foreground">
                {a.override_guidance}
              </div>
            )}
            <div className="mt-1 text-xs text-muted-foreground">
              Tier {a.tier} ({TIER_LABEL[a.tier as Tier]})
            </div>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

// ============================================================
// Sources Audit
// ============================================================

function SourcesAuditSection({ sources }: { sources: SourceCitation[] }) {
  if (sources.length === 0) return null;
  return (
    <Collapsible
      icon={<BookOpen className="h-4 w-4" />}
      title={`Sources audit (${sources.length})`}
    >
      <div className="space-y-1 text-sm">
        {sources.map((s, i) => (
          <div key={i} className="flex gap-3 items-baseline">
            <TierBadge tier={s.tier} />
            <div>
              <span className="font-medium">{s.source_id}</span>
              {s.section && (
                <span className="text-muted-foreground"> · {s.section}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

// ============================================================
// Decision Trace
// ============================================================

function DecisionTraceSection({ trace }: { trace: string[] }) {
  if (trace.length === 0) return null;
  return (
    <Collapsible
      icon={<CheckCircle2 className="h-4 w-4" />}
      title={`Decision trace (${trace.length} steps)`}
    >
      <ol className="text-xs font-mono space-y-1 text-muted-foreground">
        {trace.map((t, i) => (
          <li key={i}>
            <span className="select-none">{String(i + 1).padStart(2, "0")}.</span>{" "}
            {t}
          </li>
        ))}
      </ol>
    </Collapsible>
  );
}

// ============================================================
// Shared
// ============================================================

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-muted-foreground">{icon}</span>
          <h2 className="text-sm font-semibold uppercase tracking-wide">
            {title}
          </h2>
        </div>
        {children}
      </CardContent>
    </Card>
  );
}

function Collapsible({
  icon,
  title,
  children,
  defaultOpen = false,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card>
      <CardContent className="p-6">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 w-full text-left"
          aria-expanded={open}
        >
          <span className="text-muted-foreground">{icon}</span>
          <h2 className="text-sm font-semibold uppercase tracking-wide flex-1">
            {title}
          </h2>
          {open ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {open && <div className="mt-4">{children}</div>}
      </CardContent>
    </Card>
  );
}

function SourceTag({ source }: { source: SourceCitation }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <TierBadge tier={source.tier} />
      <span className="font-mono">{source.source_id}</span>
      {source.section && <span>· {source.section}</span>}
    </div>
  );
}

function TierBadge({ tier }: { tier: Tier }) {
  const colors: Record<Tier, string> = {
    [Tier.SA_INDUSTRY_BODY]: "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100",
    [Tier.PEER_REVIEWED_SA]: "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100",
    [Tier.INTERNATIONAL_EXT]: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100",
    [Tier.COMMERCIAL_TIER_4]: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100",
    [Tier.INFERRED_DERIVED]: "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-100",
    [Tier.IMPLEMENTER_CONVENTION]: "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  };
  return (
    <span
      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider shrink-0 ${colors[tier]}`}
    >
      T{tier}
    </span>
  );
}
