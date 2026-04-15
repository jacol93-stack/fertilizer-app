"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import type { SoilAnalysisRecord, ComparisonResult } from "./comparison-utils";
import { formatDate, getRatioName, getRatioActual } from "./comparison-utils";

const COLORS = [
  "#ff4f00", "#2563eb", "#16a34a", "#9333ea", "#dc2626",
  "#ca8a04", "#0d9488", "#c026d3", "#ea580c", "#4f46e5",
];

const PARAM_GROUPS: { title: string; params: string[] }[] = [
  { title: "pH", params: ["pH (KCl)", "pH (H2O)", "pH(KCl)", "pH(H2O)"] },
  { title: "Macronutrients", params: ["P (Bray-1)", "P(Bray1)", "P (Citric acid)", "K", "Ca", "Mg", "S"] },
  { title: "Micronutrients", params: ["Fe", "B", "Mn", "Zn", "Cu", "Mo"] },
  { title: "Organic & CEC", params: ["Org C", "CEC", "Clay%", "Clay", "Na"] },
];

function ThresholdBands({
  param,
  thresholds,
}: {
  param: string;
  thresholds: Record<string, { very_low_max: number; low_max: number; optimal_max: number; high_max: number }>;
}) {
  const t = thresholds[param];
  if (!t) return null;

  return (
    <>
      <ReferenceArea y1={0} y2={t.very_low_max} fill="#fee2e2" fillOpacity={0.4} />
      <ReferenceArea y1={t.very_low_max} y2={t.low_max} fill="#ffedd5" fillOpacity={0.4} />
      <ReferenceArea y1={t.low_max} y2={t.optimal_max} fill="#dcfce7" fillOpacity={0.4} />
      <ReferenceArea y1={t.optimal_max} y2={t.high_max} fill="#dbeafe" fillOpacity={0.4} />
    </>
  );
}

export function TrendCharts({
  data,
}: {
  data: ComparisonResult;
}) {
  const { analyses, sufficiency_thresholds } = data;

  // Build data points per analysis
  const allParams = new Set<string>();
  for (const a of analyses) {
    if (a.soil_values) {
      Object.keys(a.soil_values).forEach((k) => allParams.add(k));
    }
  }

  // Only show groups that have matching params in the data
  const activeGroups = PARAM_GROUPS.map((group) => {
    const matchedParams = group.params.filter((p) => allParams.has(p));
    return { ...group, params: matchedParams };
  }).filter((g) => g.params.length > 0);

  // Build ratio data
  const allRatios = new Set<string>();
  for (const a of analyses) {
    for (const r of a.ratio_results || []) {
      allRatios.add(getRatioName(r));
    }
  }

  return (
    <div className="space-y-4">
      {activeGroups.map((group) => {
        const chartData = analyses.map((a) => {
          const point: Record<string, unknown> = {
            date: formatDate(a.analysis_date || a.created_at),
            field: a.field || a.farm || "",
          };
          for (const param of group.params) {
            const v = a.soil_values?.[param];
            if (v != null) point[param] = Number(v);
          }
          return point;
        });

        // For single-param groups (pH), show threshold bands
        const showBands = group.params.length === 1;

        return (
          <Card key={group.title}>
            <CardHeader>
              <CardTitle>{group.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  {showBands && (
                    <ThresholdBands
                      param={group.params[0]}
                      thresholds={sufficiency_thresholds}
                    />
                  )}
                  {group.params.map((param, i) => (
                    <Line
                      key={param}
                      type="monotone"
                      dataKey={param}
                      stroke={COLORS[i % COLORS.length]}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        );
      })}

      {/* Ratio trends */}
      {allRatios.size > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Ratio Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={analyses.map((a) => {
                  const point: Record<string, unknown> = {
                    date: formatDate(a.analysis_date || a.created_at),
                  };
                  for (const r of a.ratio_results || []) {
                    const name = getRatioName(r);
                    const val = getRatioActual(r);
                    if (val != null) point[name] = val;
                  }
                  return point;
                })}
                margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                {[...allRatios].map((name, i) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
