"use client";

import { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ExtractedSample } from "../types";
import { groupSamplesByCrop } from "../helpers";

interface SamplePickerProps {
  samples: ExtractedSample[];
  onSelect: (sample: ExtractedSample, averaged?: Record<string, number>) => void;
  selectedIdx: number | null;
}

export function SamplePicker({ samples, onSelect, selectedIdx }: SamplePickerProps) {
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  const groups = useMemo(() => groupSamplesByCrop(samples as Array<{ crop?: string; values: Record<string, number> }>), [samples]);
  const groupEntries = useMemo(() => Array.from(groups.entries()), [groups]);

  if (samples.length <= 1) return null;

  // If all samples are the same crop, show flat list + averaged option
  if (groupEntries.length === 1) {
    const [cropName, group] = groupEntries[0];
    return (
      <Card className={selectedIdx != null ? "border border-muted" : "border-2 border-[var(--sapling-orange)]"}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {selectedIdx != null ? "Samples from Report" : "Select Sample to Import"}
          </CardTitle>
          <CardDescription>
            {samples.length} samples for {cropName}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Averaged option */}
          {group.samples.length > 1 && (
            <button
              onClick={() => onSelect({ crop: cropName, values: group.averaged }, group.averaged)}
              className="mb-2 flex w-full items-center justify-between rounded-md border-2 border-dashed border-[var(--sapling-orange)]/50 bg-orange-50/50 px-3 py-2 text-left text-sm font-medium text-[var(--sapling-orange)] transition-colors hover:bg-orange-50"
            >
              <span>Use averaged values ({group.samples.length} samples)</span>
              <span className="text-xs">{Object.keys(group.averaged).length} params</span>
            </button>
          )}
          <div className="max-h-48 space-y-1 overflow-y-auto">
            {samples.map((sample, i) => (
              <button
                key={i}
                onClick={() => onSelect(sample)}
                className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                  selectedIdx === i
                    ? "border-[var(--sapling-orange)] bg-orange-50 font-medium"
                    : "hover:bg-muted/50"
                }`}
              >
                <div>
                  <span className={selectedIdx === i ? "text-[var(--sapling-orange)]" : "font-medium"}>
                    {sample.block_name || sample.sample_id || `Sample ${i + 1}`}
                  </span>
                  {sample.cultivar && <span className="ml-1 text-muted-foreground">({sample.cultivar})</span>}
                </div>
                <span className="text-xs text-muted-foreground">
                  {selectedIdx === i ? "Selected" : `${Object.keys(sample.values).length} values`}
                </span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Multiple crops — show grouped
  return (
    <Card className={selectedIdx != null ? "border border-muted" : "border-2 border-[var(--sapling-orange)]"}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Samples by Crop</CardTitle>
        <CardDescription>
          {samples.length} samples across {groupEntries.length} crops
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {groupEntries.map(([cropName, group]) => (
            <div key={cropName}>
              <button
                onClick={() => setExpandedGroup(expandedGroup === cropName ? null : cropName)}
                className="flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm font-medium hover:bg-muted/50"
              >
                <div className="flex items-center gap-2">
                  {expandedGroup === cropName ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                  <span>{cropName}</span>
                  <span className="text-xs font-normal text-muted-foreground">
                    {group.samples.length} sample{group.samples.length !== 1 ? "s" : ""}
                  </span>
                </div>
                {group.samples.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect({ crop: cropName, values: group.averaged }, group.averaged);
                    }}
                    className="rounded bg-orange-50 px-2 py-0.5 text-xs font-medium text-[var(--sapling-orange)] hover:bg-orange-100"
                  >
                    Use Avg
                  </button>
                )}
              </button>
              {expandedGroup === cropName && (
                <div className="ml-6 mt-1 space-y-1">
                  {group.samples.map((s, i) => {
                    // Find original sample in full list for ExtractedSample fields
                    const original = samples.find((orig) => orig.values === s.values) || s;
                    const globalIdx = samples.indexOf(original as ExtractedSample);
                    return (
                      <button
                        key={i}
                        onClick={() => onSelect(original as ExtractedSample)}
                        className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                          selectedIdx === globalIdx
                            ? "border-[var(--sapling-orange)] bg-orange-50 font-medium"
                            : "hover:bg-muted/50"
                        }`}
                      >
                        <span>{(original as ExtractedSample).block_name || (original as ExtractedSample).sample_id || `Sample ${globalIdx + 1}`}</span>
                        <span className="text-xs text-muted-foreground">{Object.keys(s.values).length} values</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
