"use client";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SoilGaugeChart, NutrientRatioBar } from "@/components/soil-visualizations";
import { SOIL_PARAMS, PARAM_LABELS } from "../types";
import type { Classification, RatioResult } from "../types";

interface SoilResultsProps {
  classifications: Classification;
  soilValues: Record<string, string>;
  soilThresholds: Record<string, { very_low_max: number; low_max: number; optimal_max: number; high_max: number }>;
  ratios: RatioResult[];
}

export function SoilResults({
  classifications,
  soilValues,
  soilThresholds,
  ratios,
}: SoilResultsProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Classifications */}
        <Card>
          <CardHeader>
            <CardTitle>Soil Classifications</CardTitle>
            <CardDescription>Each parameter classified against sufficiency ranges</CardDescription>
          </CardHeader>
          <CardContent>
            {Object.entries(SOIL_PARAMS).map(([group, params]) => {
              const groupItems = params.filter((p) => classifications[p]);
              if (groupItems.length === 0) return null;
              return (
                <div key={group} className="mb-4 last:mb-0">
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {group}
                  </h4>
                  <div className="divide-y">
                    {groupItems.map((param) => (
                      <SoilGaugeChart
                        key={param}
                        parameter={PARAM_LABELS[param] || param}
                        value={parseFloat(soilValues[param]) || 0}
                        unit=""
                        classification={classifications[param]}
                        thresholds={soilThresholds[param]}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Ratios */}
        <Card>
          <CardHeader>
            <CardTitle>Nutrient Ratios</CardTitle>
            <CardDescription>Actual values compared to ideal ranges</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {ratios.map((r, i) => {
                const name = String(r.Ratio || r.ratio_name || "");
                const actual = (r.Actual ?? r.actual) as number | undefined;
                const idealMin = (r.Ideal_Min ?? r.ideal_low ?? r.ideal_min) as number | undefined;
                const idealMax = (r.Ideal_Max ?? r.ideal_high ?? r.ideal_max) as number | undefined;
                const status = String(r.Status || r.status || "");
                if (actual == null || idealMin == null || idealMax == null) {
                  return (
                    <div key={i} className="flex items-center justify-between px-1 py-2">
                      <span className="text-sm font-medium">{name}</span>
                      <span className="text-xs text-muted-foreground">—</span>
                    </div>
                  );
                }
                return (
                  <NutrientRatioBar
                    key={i}
                    ratio={name}
                    actual={Number(actual)}
                    ideal_min={Number(idealMin)}
                    ideal_max={Number(idealMax)}
                    unit=""
                    status={status}
                  />
                );
              })}
              {ratios.length === 0 && (
                <p className="text-sm text-muted-foreground">No ratio data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
