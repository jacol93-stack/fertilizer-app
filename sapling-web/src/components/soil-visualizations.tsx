"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// ── Brand Colors ──────────────────────────────────────────────────────────────
const BRAND_ORANGE = "#ff4f00";
const BRAND_DARK = "#191919";

// ── Classification helpers ────────────────────────────────────────────────────

function classificationBadgeClasses(c: string): string {
  const lower = c.toLowerCase();
  if (lower.includes("very low")) return "bg-red-100 text-red-700";
  if (lower.includes("low")) return "bg-orange-100 text-orange-700";
  if (lower.includes("optimal") || lower.includes("adequate"))
    return "bg-green-100 text-green-700";
  if (lower.includes("very high")) return "bg-purple-100 text-purple-700";
  if (lower.includes("high")) return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}

function statusBadgeClasses(s: string): string {
  const lower = s.toLowerCase();
  if (lower === "ideal" || lower === "optimal" || lower === "ok")
    return "bg-green-100 text-green-700";
  if (lower.includes("below") || lower === "low")
    return "bg-orange-100 text-orange-700";
  if (lower.includes("above") || lower === "high")
    return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}

// Zone colors for gauge
const ZONE_COLORS = {
  very_low: "#ef4444", // red-500
  low: "#f97316", // orange-500
  optimal: "#22c55e", // green-500
  high: "#3b82f6", // blue-500
  very_high: "#a855f7", // purple-500
};

// ── 1. SoilGaugeChart ─────────────────────────────────────────────────────────

interface SoilGaugeChartProps {
  parameter: string;
  value: number;
  unit: string;
  classification: string;
  thresholds?: {
    very_low_max: number;
    low_max: number;
    optimal_max: number;
    high_max: number;
  };
}

export function SoilGaugeChart({
  parameter,
  value,
  unit,
  classification,
  thresholds,
}: SoilGaugeChartProps) {
  if (!thresholds) {
    // No thresholds: just show parameter name, value, and classification badge
    return (
      <div className="flex items-center justify-between py-2 px-1">
        <span className="text-sm font-medium text-foreground truncate mr-2">
          {parameter}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-sm tabular-nums">
            {value} {unit}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${classificationBadgeClasses(classification)}`}
          >
            {classification}
          </span>
        </div>
      </div>
    );
  }

  // Build zone widths as percentages of the full range
  // The very_high zone extends 25% beyond high_max for visual purposes
  const maxVal = thresholds.high_max * 1.25;
  const zones = [
    { key: "very_low", end: thresholds.very_low_max, color: ZONE_COLORS.very_low },
    { key: "low", end: thresholds.low_max, color: ZONE_COLORS.low },
    { key: "optimal", end: thresholds.optimal_max, color: ZONE_COLORS.optimal },
    { key: "high", end: thresholds.high_max, color: ZONE_COLORS.high },
    { key: "very_high", end: maxVal, color: ZONE_COLORS.very_high },
  ];

  // Compute widths
  let prev = 0;
  const zoneWidths = zones.map((z) => {
    const width = ((z.end - prev) / maxVal) * 100;
    prev = z.end;
    return { ...z, widthPct: Math.max(width, 0) };
  });

  // Marker position (clamp between 0 and 100)
  const markerPct = Math.min(Math.max((value / maxVal) * 100, 0), 100);

  return (
    <div className="py-2 px-1">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-medium text-foreground truncate mr-2">
          {parameter}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-sm tabular-nums">
            {value} {unit}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${classificationBadgeClasses(classification)}`}
          >
            {classification}
          </span>
        </div>
      </div>
      <div className="relative w-full h-3 rounded-full overflow-hidden flex">
        {zoneWidths.map((z) => (
          <div
            key={z.key}
            className="h-full"
            style={{ width: `${z.widthPct}%`, backgroundColor: z.color }}
          />
        ))}
        {/* Marker needle */}
        <div
          className="absolute top-0 h-full w-0.5 bg-foreground"
          style={{ left: `${markerPct}%`, transform: "translateX(-50%)" }}
        />
        <div
          className="absolute -top-1 w-0 h-0"
          style={{
            left: `${markerPct}%`,
            transform: "translateX(-50%)",
            borderLeft: "4px solid transparent",
            borderRight: "4px solid transparent",
            borderTop: `5px solid ${BRAND_DARK}`,
          }}
        />
      </div>
    </div>
  );
}

// ── 2. NutrientRatioBar ───────────────────────────────────────────────────────

interface NutrientRatioBarProps {
  ratio: string;
  actual: number;
  ideal_min: number;
  ideal_max: number;
  unit: string;
  status: string;
}

export function NutrientRatioBar({
  ratio,
  actual,
  ideal_min,
  ideal_max,
  unit,
  status,
}: NutrientRatioBarProps) {
  // Visual range: 0 to 2x ideal_max (or at least enough to show the actual value)
  const rangeMax = Math.max(ideal_max * 2, actual * 1.2, ideal_max + (ideal_max - ideal_min) * 2);
  const rangeMin = 0;
  const total = rangeMax - rangeMin;

  const idealStartPct = ((ideal_min - rangeMin) / total) * 100;
  const idealWidthPct = ((ideal_max - ideal_min) / total) * 100;
  const markerPct = Math.min(Math.max(((actual - rangeMin) / total) * 100, 0), 100);

  return (
    <div className="py-2 px-1">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-medium text-foreground truncate mr-2">
          {ratio}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-sm tabular-nums">
            {actual.toFixed(2)} {unit}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadgeClasses(status)}`}
          >
            {status}
          </span>
        </div>
      </div>
      <div className="relative w-full h-3 rounded-full bg-gray-200 overflow-hidden">
        {/* Below-ideal zone (red tint) */}
        <div
          className="absolute top-0 h-full rounded-l-full"
          style={{
            left: "0%",
            width: `${idealStartPct}%`,
            backgroundColor: "#fecaca", // red-200
          }}
        />
        {/* Ideal zone (green) */}
        <div
          className="absolute top-0 h-full"
          style={{
            left: `${idealStartPct}%`,
            width: `${idealWidthPct}%`,
            backgroundColor: ZONE_COLORS.optimal,
          }}
        />
        {/* Above-ideal zone (blue tint) */}
        <div
          className="absolute top-0 h-full rounded-r-full"
          style={{
            left: `${idealStartPct + idealWidthPct}%`,
            width: `${100 - idealStartPct - idealWidthPct}%`,
            backgroundColor: "#bfdbfe", // blue-200
          }}
        />
        {/* Marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-foreground"
          style={{ left: `${markerPct}%`, transform: "translateX(-50%)" }}
        />
        <div
          className="absolute -top-1 w-0 h-0"
          style={{
            left: `${markerPct}%`,
            transform: "translateX(-50%)",
            borderLeft: "4px solid transparent",
            borderRight: "4px solid transparent",
            borderTop: `5px solid ${BRAND_DARK}`,
          }}
        />
      </div>
      <div className="flex justify-between mt-1 text-[10px] text-muted-foreground tabular-nums">
        <span>{ideal_min.toFixed(1)}</span>
        <span>{ideal_max.toFixed(1)}</span>
      </div>
    </div>
  );
}

// ── 3. NutrientTargetChart ────────────────────────────────────────────────────

interface NutrientTargetChartProps {
  targets: Array<{
    Nutrient: string;
    Target_kg_ha: number;
    Ratio_Adjustment_kg_ha: number;
    Final_Target_kg_ha: number;
  }>;
}

export function NutrientTargetChart({ targets }: NutrientTargetChartProps) {
  const data = targets.map((t) => ({
    nutrient: t.Nutrient,
    base: t.Target_kg_ha,
    adjustment: t.Ratio_Adjustment_kg_ha,
    final: t.Final_Target_kg_ha,
  }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="nutrient"
            tick={{ fontSize: 12, fill: BRAND_DARK }}
            axisLine={{ stroke: "#d1d5db" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: BRAND_DARK }}
            axisLine={{ stroke: "#d1d5db" }}
            label={{
              value: "kg/ha",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 11, fill: BRAND_DARK },
            }}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e5e7eb",
            }}
            formatter={(val, name) => {
              const num = Number(val) || 0;
              const label =
                name === "base"
                  ? "Base Target"
                  : name === "adjustment"
                    ? "Ratio Adjustment"
                    : "Final Target";
              return [num.toFixed(1) + " kg/ha", label];
            }}
          />
          <Legend
            formatter={(val: string) =>
              val === "base"
                ? "Base Target"
                : val === "adjustment"
                  ? "Ratio Adjustment"
                  : "Final Target"
            }
            wrapperStyle={{ fontSize: 12 }}
          />
          <Bar
            dataKey="base"
            stackId="target"
            fill={BRAND_ORANGE}
            radius={[0, 0, 0, 0]}
            name="base"
          />
          <Bar
            dataKey="adjustment"
            stackId="target"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            name="adjustment"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── 4. NutrientDeliveryChart ──────────────────────────────────────────────────

interface NutrientDeliveryChartProps {
  applications: Array<{
    month_name: string;
    n_kg_ha: number;
    p_kg_ha: number;
    k_kg_ha: number;
  }>;
  idealItems?: Array<{
    month_target: number;
    n_kg_ha: number;
    p_kg_ha: number;
    k_kg_ha: number;
  }>;
}

const MONTH_NAMES_SHORT = [
  "",
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function NutrientDeliveryChart({
  applications,
  idealItems,
}: NutrientDeliveryChartProps) {
  // Build data from applications
  const data = applications.map((app) => {
    const row: Record<string, string | number> = {
      month: app.month_name,
      N: app.n_kg_ha,
      P: app.p_kg_ha,
      K: app.k_kg_ha,
    };
    // If idealItems, find matching month and add ideal values
    if (idealItems) {
      const ideal = idealItems.find(
        (it) =>
          it.month_target != null &&
          MONTH_NAMES_SHORT[it.month_target] === app.month_name
      );
      if (ideal) {
        row.N_ideal = ideal.n_kg_ha;
        row.P_ideal = ideal.p_kg_ha;
        row.K_ideal = ideal.k_kg_ha;
      }
    }
    return row;
  });

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12, fill: BRAND_DARK }}
            axisLine={{ stroke: "#d1d5db" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: BRAND_DARK }}
            axisLine={{ stroke: "#d1d5db" }}
            label={{
              value: "kg/ha",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 11, fill: BRAND_DARK },
            }}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e5e7eb",
            }}
            formatter={(val, name) => [
              (Number(val) || 0).toFixed(1) + " kg/ha",
              String(name),
            ]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="N" fill="#22c55e" name="N" />
          <Bar dataKey="P" fill="#3b82f6" name="P" />
          <Bar dataKey="K" fill={BRAND_ORANGE} name="K" />
          {idealItems && (
            <>
              <Bar dataKey="N_ideal" fill="#86efac" name="N (ideal)" opacity={0.5} />
              <Bar dataKey="P_ideal" fill="#93c5fd" name="P (ideal)" opacity={0.5} />
              <Bar dataKey="K_ideal" fill="#fdba74" name="K (ideal)" opacity={0.5} />
            </>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── 5. SeasonTimeline ─────────────────────────────────────────────────────────

interface SeasonTimelineProps {
  applications: Array<{
    month: number;
    month_name: string;
    stage_names: string[];
    blend_group: string;
    n_kg_ha: number;
    k_kg_ha: number;
  }>;
}

const ALL_MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Stable color palette for growth stages
const STAGE_COLORS = [
  "#fef3c7", // amber-100
  "#d1fae5", // emerald-100
  "#dbeafe", // blue-100
  "#fce7f3", // pink-100
  "#e0e7ff", // indigo-100
  "#fef9c3", // yellow-100
  "#ccfbf1", // teal-100
  "#ede9fe", // violet-100
];

export function SeasonTimeline({ applications }: SeasonTimelineProps) {
  const currentMonth = new Date().getMonth() + 1; // 1-indexed

  // Build a map from month number to application data
  const appByMonth = new Map(applications.map((a) => [a.month, a]));

  // Collect all unique stage names and assign colors
  const allStages: string[] = [];
  applications.forEach((a) => {
    a.stage_names.forEach((s) => {
      if (!allStages.includes(s)) allStages.push(s);
    });
  });
  const stageColorMap = new Map<string, string>();
  allStages.forEach((s, i) => {
    stageColorMap.set(s, STAGE_COLORS[i % STAGE_COLORS.length]);
  });

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-[600px]">
        {/* Month headers */}
        <div className="grid grid-cols-12 gap-0.5 mb-1">
          {ALL_MONTHS.map((m, i) => {
            const monthNum = i + 1;
            const isCurrent = monthNum === currentMonth;
            return (
              <div
                key={m}
                className={`text-center text-xs font-medium py-1 rounded-t ${
                  isCurrent
                    ? "bg-orange-500 text-white"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {m}
              </div>
            );
          })}
        </div>

        {/* Growth stage blocks */}
        <div className="grid grid-cols-12 gap-0.5 mb-1">
          {ALL_MONTHS.map((_, i) => {
            const monthNum = i + 1;
            const app = appByMonth.get(monthNum);
            if (!app || app.stage_names.length === 0) {
              return (
                <div
                  key={monthNum}
                  className="h-6 bg-gray-50 rounded-sm border border-gray-100"
                />
              );
            }
            const stageName = app.stage_names[0];
            const bgColor = stageColorMap.get(stageName) || "#f3f4f6";
            return (
              <div
                key={monthNum}
                className="h-6 rounded-sm border border-gray-200 flex items-center justify-center"
                style={{ backgroundColor: bgColor }}
                title={app.stage_names.join(", ")}
              >
                <span className="text-[9px] leading-none truncate px-0.5 text-gray-700">
                  {stageName.length > 5
                    ? stageName.slice(0, 5) + "."
                    : stageName}
                </span>
              </div>
            );
          })}
        </div>

        {/* Application dots */}
        <div className="grid grid-cols-12 gap-0.5">
          {ALL_MONTHS.map((_, i) => {
            const monthNum = i + 1;
            const app = appByMonth.get(monthNum);
            return (
              <div
                key={monthNum}
                className="flex items-center justify-center h-8"
              >
                {app ? (
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm"
                    style={{ backgroundColor: BRAND_ORANGE }}
                    title={`${app.blend_group}: N=${app.n_kg_ha}, K=${app.k_kg_ha} kg/ha`}
                  >
                    {app.blend_group}
                  </div>
                ) : (
                  <div className="w-2 h-2 rounded-full bg-gray-200" />
                )}
              </div>
            );
          })}
        </div>

        {/* Stage legend */}
        {allStages.length > 0 && (
          <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-600">
            {allStages.map((s) => (
              <div key={s} className="flex items-center gap-1">
                <div
                  className="w-3 h-3 rounded-sm border border-gray-200"
                  style={{ backgroundColor: stageColorMap.get(s) }}
                />
                <span>{s}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
