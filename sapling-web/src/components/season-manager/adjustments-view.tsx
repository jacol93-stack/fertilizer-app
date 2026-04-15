"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, Upload, AlertTriangle } from "lucide-react";
import type { ProgrammeAdjustment } from "@/lib/season-constants";

interface AdjustmentsViewProps {
  programmeId: string;
}

export function AdjustmentsView({ programmeId }: AdjustmentsViewProps) {
  const [adjustments, setAdjustments] = useState<ProgrammeAdjustment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ProgrammeAdjustment[]>(`/api/programmes/${programmeId}/adjustments`)
      .then(setAdjustments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [programmeId]);

  const triggerLabel = (type: string) => {
    switch (type) {
      case "leaf_analysis": return "Leaf Analysis";
      case "observation": return "Field Observation";
      case "weather": return "Weather Event";
      case "manual": return "Manual Adjustment";
      default: return type;
    }
  };

  const triggerColor = (type: string) => {
    switch (type) {
      case "leaf_analysis": return "bg-green-100 text-green-700";
      case "observation": return "bg-blue-100 text-blue-700";
      case "weather": return "bg-amber-100 text-amber-700";
      default: return "bg-gray-100 text-gray-700";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Mid-Season Adjustments</h3>
          <p className="text-sm text-muted-foreground">
            Upload a new analysis to compare and get adjustment recommendations
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => window.location.href = `/season-manager/${programmeId}/upload`}
        >
          <Upload className="size-4" />
          Upload New Analysis
        </Button>
      </div>

      {adjustments.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No adjustments made yet
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {adjustments.map((adj) => (
            <Card key={adj.id}>
              <CardContent className="py-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${triggerColor(adj.trigger_type)}`}>
                        {triggerLabel(adj.trigger_type)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(adj.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {adj.notes && (
                      <p className="mt-1 text-sm">{adj.notes}</p>
                    )}
                    {adj.adjustment_data && typeof adj.adjustment_data === "object" ? (
                      <div className="mt-2 rounded border bg-muted/30 px-3 py-2 text-xs">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(adj.adjustment_data, null, 2)}
                        </pre>
                      </div>
                    ) : null}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
