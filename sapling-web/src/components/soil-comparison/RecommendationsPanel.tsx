"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Lightbulb, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { Recommendation } from "./comparison-utils";

const ICONS = {
  info: Info,
  warning: AlertTriangle,
  success: CheckCircle2,
};

const BORDER_COLORS = {
  info: "border-l-blue-400",
  warning: "border-l-orange-400",
  success: "border-l-green-400",
};

const ICON_COLORS = {
  info: "text-blue-500",
  warning: "text-orange-500",
  success: "text-green-500",
};

export function RecommendationsPanel({
  recommendations,
}: {
  recommendations: Recommendation[];
}) {
  if (recommendations.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="size-4 text-[var(--sapling-orange)]" />
          Observations & Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {recommendations.map((rec, i) => {
            const Icon = ICONS[rec.type] || Info;
            return (
              <div
                key={i}
                className={`flex items-start gap-3 rounded-lg border-l-4 bg-gray-50 px-4 py-3 ${BORDER_COLORS[rec.type]}`}
              >
                <Icon
                  className={`mt-0.5 size-4 shrink-0 ${ICON_COLORS[rec.type]}`}
                />
                <p className="text-sm text-[var(--sapling-dark)]">
                  {rec.message}
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
