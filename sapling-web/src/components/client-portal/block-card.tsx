"use client";

import Link from "next/link";
import { AlertTriangle, CheckCircle, Droplet, FlaskConical, Leaf, TrendingUp, MapPin } from "lucide-react";
import { Sparkline } from "@/components/dashboard/sparkline";
import type { Field } from "@/lib/season-constants";

export interface BlockCardData {
  field: Field;
  /** Most-recent soil pH (or N) — shown as the headline soil number. */
  latestSoil?: { date: string; ph: number | null; oc: number | null; n: number | null };
  soilHistory?: number[];
  /** Most-recent leaf classification summary, e.g. "Adq" or "Low N · Adq P". */
  latestLeaf?: { date: string; summary: string };
  leafHistory?: number[];
  /** Most-recent yield kg/ha + benchmark band. */
  latestYield?: { season: string; tHa: number | null; benchmark?: { low: number; typical: number; high: number } };
  yieldHistory?: number[];
  /** Counts surfaced under the latest-row when the block carries
   * historical data — gives the user a quick "how much do we know
   * about this block" read at a glance. */
  soilCount?: number;
  leafCount?: number;
  yieldCount?: number;
}

const HEALTH_LABELS: Record<string, string> = {
  size: "size",
  crop: "crop",
  soil_analysis: "soil analysis",
  soil_macros_missing: "soil macros",
  tree_age: "tree age",
  planting_date: "planting date",
  yield_target: "yield target",
  irrigation_type: "irrigation",
  accepted_methods: "methods",
  pop_per_ha: "trees / ha",
  soil_pH_missing: "pH",
  soil_CEC_missing: "CEC",
};

function MiniHealthPill({ health }: { health: NonNullable<Field["health"]> }) {
  if (health.level === "ok") {
    return (
      <span
        className="inline-flex items-center gap-0.5 rounded-full bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-700"
        title="All engine-relevant inputs present"
      >
        <CheckCircle className="size-2.5" />
        Ready
      </span>
    );
  }
  if (health.level === "critical") {
    const label = health.critical
      .map((k) => HEALTH_LABELS[k] ?? k)
      .slice(0, 2)
      .join(", ");
    return (
      <span
        className="inline-flex items-center gap-0.5 rounded-full bg-red-50 px-1.5 py-0.5 text-[9px] font-semibold text-red-700"
        title={`Engine can't build until: ${health.critical.map((k) => HEALTH_LABELS[k] ?? k).join(", ")}`}
      >
        <AlertTriangle className="size-2.5" />
        {label}{health.critical.length > 2 && ` +${health.critical.length - 2}`}
      </span>
    );
  }
  const label = health.warnings
    .map((k) => HEALTH_LABELS[k] ?? k)
    .slice(0, 1)
    .join(", ");
  return (
    <span
      className="inline-flex items-center gap-0.5 rounded-full bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold text-amber-700"
      title={`Programme will assume: ${health.warnings.map((k) => HEALTH_LABELS[k] ?? k).join(", ")}`}
    >
      <AlertTriangle className="size-2.5" />
      {label}{health.warnings.length > 1 && ` +${health.warnings.length - 1}`}
    </span>
  );
}

export function BlockCard({
  clientId,
  data,
  selectable,
  selected,
  onToggleSelect,
}: {
  clientId: string;
  data: BlockCardData;
  /** When true, the card renders as a button that toggles `selected`
   * instead of navigating to the field detail page. Drives bulk-delete
   * mode in the Farms & Blocks list. */
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: () => void;
}) {
  const { field, latestSoil, latestLeaf, latestYield, soilHistory, leafHistory, yieldHistory } = data;
  const cropBadge = field.crop ? (
    <span
      className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
        field.crop_type === "perennial"
          ? "bg-purple-50 text-purple-700"
          : "bg-green-50 text-green-700"
      }`}
    >
      {field.crop}
      {field.cultivar && <span className="ml-1 opacity-70">· {field.cultivar}</span>}
    </span>
  ) : (
    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
      No crop set
    </span>
  );

  const irrigationLabel = field.irrigation_type && field.irrigation_type !== "none"
    ? field.irrigation_type
    : null;

  const yieldPct =
    latestYield?.tHa != null && latestYield.benchmark?.typical
      ? Math.round((latestYield.tHa / latestYield.benchmark.typical) * 100)
      : null;

  const inner = (
    <>
      {selectable && (
        <div
          className={`absolute right-2.5 top-2.5 z-10 flex size-4 items-center justify-center rounded-full border-2 ${
            selected
              ? "border-[var(--sapling-orange)] bg-[var(--sapling-orange)]"
              : "border-gray-300 bg-white"
          }`}
        >
          {selected && <span className="text-[8px] leading-none text-white">✓</span>}
        </div>
      )}
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 truncate text-sm font-semibold text-[var(--sapling-dark)]">
            {field.name}
            {field.health && <MiniHealthPill health={field.health} />}
          </div>
          <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
            {field.size_ha != null && <span>{field.size_ha} ha</span>}
            {field.tree_age != null && <span>· {field.tree_age}yr</span>}
            {field.pop_per_ha != null && <span>· {field.pop_per_ha}/ha</span>}
            {irrigationLabel && (
              <span className="inline-flex items-center gap-0.5 text-cyan-600">
                <Droplet className="size-2.5" /> {irrigationLabel}
              </span>
            )}
          </div>
        </div>
        {cropBadge}
      </div>

      <div className="mt-1 space-y-1.5 border-t pt-2 text-[11px]">
        <Row
          icon={<FlaskConical className="size-3 text-amber-600" />}
          label="Soil"
          value={
            latestSoil
              ? `pH ${latestSoil.ph?.toFixed(1) ?? "—"} · ${formatRelative(latestSoil.date)}`
              : "no analysis"
          }
          spark={soilHistory}
          dim={!latestSoil}
        />
        <Row
          icon={<Leaf className="size-3 text-emerald-600" />}
          label="Leaf"
          value={
            latestLeaf
              ? `${latestLeaf.summary} · ${formatRelative(latestLeaf.date)}`
              : "no analysis"
          }
          spark={leafHistory}
          dim={!latestLeaf}
        />
        <Row
          icon={<TrendingUp className="size-3 text-orange-600" />}
          label="Yield"
          value={
            latestYield?.tHa != null
              ? `${latestYield.tHa.toFixed(1)} t/ha${
                  yieldPct != null ? ` · ${yieldPct}%` : ""
                } · ${latestYield.season}`
              : "no record"
          }
          spark={yieldHistory}
          dim={latestYield?.tHa == null}
        />
      </div>

      {(field.gps_lat != null && field.gps_lng != null) && (
        <div className="mt-2 inline-flex items-center gap-1 text-[10px] text-muted-foreground">
          <MapPin className="size-2.5" />
          {field.gps_lat.toFixed(4)}, {field.gps_lng.toFixed(4)}
        </div>
      )}
    </>
  );

  const cardClass = `group relative flex flex-col rounded-lg border bg-white p-3.5 transition-all hover:border-[var(--sapling-orange)]/50 hover:shadow-md ${
    selected ? "ring-2 ring-[var(--sapling-orange)]" : ""
  }`;
  if (selectable) {
    return (
      <button
        type="button"
        onClick={onToggleSelect}
        className={`${cardClass} cursor-pointer text-left`}
      >
        {inner}
      </button>
    );
  }
  return (
    <Link href={`/clients/${clientId}/fields/${field.id}`} className={cardClass}>
      {inner}
    </Link>
  );
}

function Row({
  icon,
  label,
  value,
  spark,
  dim,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  spark?: number[];
  dim?: boolean;
}) {
  return (
    <div className={`flex items-center gap-2 ${dim ? "opacity-60" : ""}`}>
      <span className="flex w-9 shrink-0 items-center gap-1">
        {icon}
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
      </span>
      <span className="min-w-0 flex-1 truncate text-[11px] text-[var(--sapling-dark)]">
        {value}
      </span>
      {spark && spark.length > 1 && (
        <span className="shrink-0">
          <Sparkline
            points={spark.map((v, i) => ({ label: String(i), value: v }))}
            width={42}
            height={14}
            showSinglePoint={false}
          />
        </span>
      )}
    </div>
  );
}

function formatRelative(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days < 1) return "today";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}
