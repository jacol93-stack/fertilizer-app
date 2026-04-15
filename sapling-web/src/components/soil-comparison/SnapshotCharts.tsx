"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
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
import type { ComparisonResult } from "./comparison-utils";
import { getRatioName, getRatioActual } from "./comparison-utils";

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

function getFieldLabel(a: { field?: string | null; farm?: string | null; crop?: string | null }): string {
  const parts = [a.field || a.farm || "Unknown"];
  if (a.crop) parts.push(a.crop);
  return parts.join(" — ");
}

export function SnapshotCharts({ data }: { data: ComparisonResult }) {
  const { analyses } = data;

  // Build labels for each analysis
  const labels = analyses.map((a) => getFieldLabel(a));

  // Collect all params present
  const allParams = new Set<string>();
  for (const a of analyses) {
    if (a.soil_values) Object.keys(a.soil_values).forEach((k) => allParams.add(k));
  }

  const activeGroups = PARAM_GROUPS.map((group) => ({
    ...group,
    params: group.params.filter((p) => allParams.has(p)),
  })).filter((g) => g.params.length > 0);

  // Ratio data
  const allRatios = new Set<string>();
  for (const a of analyses) {
    for (const r of a.ratio_results || []) allRatios.add(getRatioName(r));
  }

  return (
    <div className="space-y-4">
      {activeGroups.map((group) => {
        // For bar charts: each parameter is a group on x-axis, each analysis is a bar
        const chartData = group.params.map((param) => {
          const point: Record<string, unknown> = { parameter: param };
          analyses.forEach((a, i) => {
            const v = a.soil_values?.[param];
            if (v != null) point[labels[i]] = Number(v);
          });
          return point;
        });

        return (
          <Card key={group.title}>
            <CardHeader>
              <CardTitle>{group.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="parameter" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {labels.map((label, i) => (
                    <Bar
                      key={label}
                      dataKey={label}
                      fill={COLORS[i % COLORS.length]}
                      radius={[2, 2, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        );
      })}

      {/* Ratio comparison */}
      {allRatios.size > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Ratio Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[...allRatios].map((name) => {
                  const point: Record<string, unknown> = { ratio: name };
                  analyses.forEach((a, i) => {
                    const r = (a.ratio_results || []).find((r) => getRatioName(r) === name);
                    if (r) point[labels[i]] = getRatioActual(r);
                  });
                  return point;
                })}
                margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="ratio" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {labels.map((label, i) => (
                  <Bar
                    key={label}
                    dataKey={label}
                    fill={COLORS[i % COLORS.length]}
                    radius={[2, 2, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
