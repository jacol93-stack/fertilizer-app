"use client";

import { ComboBox } from "@/components/client-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Plus, Trash2 } from "lucide-react";
import type { Block, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { emptyBlock } from "@/lib/season-constants";

interface BlockEditorProps {
  blocks: Omit<Block, "id">[];
  setBlocks: React.Dispatch<React.SetStateAction<Omit<Block, "id">[]>>;
  crops: CropNorm[];
  availableAnalyses?: SoilAnalysis[];
  minimal?: boolean; // Cold start: hide analysis linking
}

export function BlockEditor({ blocks, setBlocks, crops, availableAnalyses = [], minimal }: BlockEditorProps) {
  const updateBlock = (idx: number, updates: Partial<Block>) => {
    setBlocks((prev) => prev.map((b, i) => (i === idx ? { ...b, ...updates } : b)));
  };

  return (
    <div className="space-y-4">
      {blocks.map((block, idx) => (
        <Card key={idx} className="bg-muted/30">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Block {idx + 1}</CardTitle>
              {blocks.length > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setBlocks((prev) => prev.filter((_, i) => i !== idx))}
                >
                  <Trash2 className="size-3.5 text-red-500" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label>Block Name</Label>
                <Input
                  value={block.name}
                  onChange={(e) => updateBlock(idx, { name: e.target.value })}
                  placeholder="e.g. Block A, Lower Orchard"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Area (ha)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={block.area_ha ?? ""}
                  onChange={(e) =>
                    updateBlock(idx, { area_ha: e.target.value ? parseFloat(e.target.value) : null })
                  }
                  placeholder="0.0"
                />
              </div>
              <div className="space-y-1.5">
                <ComboBox
                  label="Crop"
                  placeholder="Select crop..."
                  items={crops.map((c) => ({ name: c.crop, value: c.crop }))}
                  value={block.crop}
                  onChange={(val) => updateBlock(idx, { crop: val })}
                  onSelect={(item) => {
                    const crop = crops.find((c) => c.crop === (item.value as string));
                    updateBlock(idx, { crop: item.value as string, yield_unit: crop?.yield_unit || "" });
                  }}
                />
              </div>
            </div>
            {!minimal && (
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label>Cultivar</Label>
                  <Input
                    value={block.cultivar}
                    onChange={(e) => updateBlock(idx, { cultivar: e.target.value })}
                    placeholder="Optional"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Yield Target {block.yield_unit && `(${block.yield_unit})`}</Label>
                  <Input
                    type="number"
                    value={block.yield_target ?? ""}
                    onChange={(e) =>
                      updateBlock(idx, { yield_target: e.target.value ? parseFloat(e.target.value) : null })
                    }
                    placeholder="0"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Tree Age (years)</Label>
                  <Input
                    type="number"
                    value={block.tree_age ?? ""}
                    onChange={(e) =>
                      updateBlock(idx, { tree_age: e.target.value ? parseInt(e.target.value) : null })
                    }
                    placeholder="Perennials only"
                  />
                </div>
              </div>
            )}
            {!minimal && availableAnalyses.length > 0 && (
              <div className="space-y-1.5">
                <Label>Link Soil Analysis</Label>
                <select
                  value={block.soil_analysis_id || ""}
                  onChange={(e) => updateBlock(idx, { soil_analysis_id: e.target.value || null })}
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                >
                  <option value="">None — enter targets later</option>
                  {availableAnalyses.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.crop || "Unknown crop"} — {a.field || "No field"} —{" "}
                      {new Date(a.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
      <Button
        variant="outline"
        onClick={() => setBlocks((prev) => [...prev, emptyBlock()])}
        className="w-full"
      >
        <Plus className="size-4" />
        Add Block
      </Button>
    </div>
  );
}
