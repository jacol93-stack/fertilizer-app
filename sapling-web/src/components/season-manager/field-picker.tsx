"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  Check,
  ChevronDown,
  ChevronUp,
  Leaf,
  Loader2,
  Plus,
  AlertCircle,
  CheckCircle2,
  MapPin,
} from "lucide-react";
import { ComboBox } from "@/components/client-selector";
import type { Block, CropNorm, SoilAnalysis } from "@/lib/season-constants";
import { blockCompleteness } from "@/lib/block-completeness";

interface FieldRow {
  id: string;
  name: string;
  size_ha: number | null;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  tree_age: number | null;
  pop_per_ha: number | null;
  latest_analysis_id: string | null;
  farm_id: string;
  farm_name?: string;
}

interface FieldPickerProps {
  farmId: string;
  farmName: string;
  blocks: Omit<Block, "id">[];
  setBlocks: React.Dispatch<React.SetStateAction<Omit<Block, "id">[]>>;
  crops: CropNorm[];
  analyses: SoilAnalysis[];
  otherFarms?: Array<{ id: string; name: string }>;
}

export function FieldPicker({
  farmId,
  farmName,
  blocks,
  setBlocks,
  crops,
  analyses,
  otherFarms = [],
}: FieldPickerProps) {
  const [fields, setFields] = useState<FieldRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [otherFarmFields, setOtherFarmFields] = useState<Record<string, FieldRow[]>>({});
  const [otherFarmOpen, setOtherFarmOpen] = useState<Record<string, boolean>>({});

  // Load the main farm's fields. Nothing is pre-selected — the agent
  // ticks the fields they want included in this programme. Keeps them
  // in control of scope, especially when a farm has many fields and
  // only a subset is being planned this season.
  useEffect(() => {
    if (!farmId) { setFields([]); setLoading(false); return; }
    setLoading(true);
    api.get<FieldRow[]>(`/api/clients/farms/${farmId}/fields`)
      .then((data) => {
        const rows = (data || []).map((f) => ({ ...f, farm_id: farmId, farm_name: farmName }));
        setFields(rows);
      })
      .catch(() => toast.error("Failed to load farm fields"))
      .finally(() => setLoading(false));
  }, [farmId]);

  const selectedByFieldId = useMemo(() => {
    const map: Record<string, Omit<Block, "id">> = {};
    for (const b of blocks) {
      if (b.field_id) map[b.field_id] = b;
    }
    return map;
  }, [blocks]);

  const toggle = (field: FieldRow, include: boolean) => {
    if (include) {
      setBlocks((prev) => {
        if (prev.some((b) => b.field_id === field.id)) return prev;
        return [...prev, rowToBlock(field)];
      });
    } else {
      setBlocks((prev) => prev.filter((b) => b.field_id !== field.id));
    }
  };

  const selectAll = () => {
    const existing = new Set(blocks.filter((b) => b.field_id).map((b) => b.field_id));
    const toAdd = fields.filter((f) => !existing.has(f.id)).map(rowToBlock);
    if (!toAdd.length) return;
    setBlocks((prev) => [...prev, ...toAdd]);
  };

  const deselectAll = () => {
    setBlocks((prev) => prev.filter((b) => !b.field_id || !fields.some((f) => f.id === b.field_id)));
  };

  const updateBlock = (fieldId: string, patch: Partial<Block>) => {
    setBlocks((prev) =>
      prev.map((b) => (b.field_id === fieldId ? { ...b, ...patch } : b))
    );
  };

  const loadOtherFarm = async (otherFarmId: string, name: string) => {
    setOtherFarmOpen((prev) => ({ ...prev, [otherFarmId]: !prev[otherFarmId] }));
    if (otherFarmFields[otherFarmId]) return;
    try {
      const data = await api.get<FieldRow[]>(`/api/clients/farms/${otherFarmId}/fields`);
      const rows = (data || []).map((f) => ({ ...f, farm_id: otherFarmId, farm_name: name }));
      setOtherFarmFields((prev) => ({ ...prev, [otherFarmId]: rows }));
    } catch {
      toast.error(`Failed to load ${name}`);
    }
  };

  const addCustomBlock = () => {
    setBlocks((prev) => [
      ...prev,
      {
        name: `Block ${prev.length + 1}`,
        area_ha: null,
        crop: "",
        cultivar: "",
        yield_target: null,
        yield_unit: "",
        tree_age: null,
        pop_per_ha: null,
        soil_analysis_id: null,
        notes: "",
        field_id: null,
      },
    ]);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const selectedCount = blocks.filter((b) => b.field_id).length;

  return (
    <div className="space-y-4">
      {/* Main farm: header + bulk actions */}
      {fields.length > 0 && (
        <div>
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <MapPin className="size-4 text-muted-foreground" />
              <span className="font-medium text-[var(--sapling-dark)]">{farmName || "Farm"}</span>
              <span className="text-xs text-muted-foreground">
                {selectedCount === 0
                  ? `· tick the ${fields.length} field${fields.length !== 1 ? "s" : ""} to include`
                  : `· ${selectedCount} of ${fields.length} selected`}
              </span>
            </div>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" onClick={selectAll} className="h-7 text-xs">
                Select all
              </Button>
              <Button variant="ghost" size="sm" onClick={deselectAll} className="h-7 text-xs">
                Clear
              </Button>
            </div>
          </div>
          <div className="space-y-1.5">
            {fields.map((f) => (
              <FieldRowCard
                key={f.id}
                field={f}
                selected={!!selectedByFieldId[f.id]}
                block={selectedByFieldId[f.id]}
                onToggle={(v) => toggle(f, v)}
                onUpdate={(p) => updateBlock(f.id, p)}
                expanded={expanded === f.id}
                onExpand={() => setExpanded(expanded === f.id ? null : f.id)}
                crops={crops}
                analyses={analyses.filter((a) => !a.field_id || a.field_id === f.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Other farms on this client */}
      {otherFarms.length > 0 && (
        <div className={fields.length > 0 ? "border-t pt-4" : ""}>
          <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            {fields.length > 0
              ? "Other farms on this client"
              : "Farms on this client"}
          </p>
          <div className="space-y-2">
            {otherFarms
              .filter((fm) => fm.id !== farmId)
              .map((fm) => {
                const isOpen = !!otherFarmOpen[fm.id];
                const list = otherFarmFields[fm.id] || [];
                return (
                  <div key={fm.id} className="rounded-lg border">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted/30"
                      onClick={() => loadOtherFarm(fm.id, fm.name)}
                    >
                      <span className="flex items-center gap-2">
                        <MapPin className="size-3.5 text-muted-foreground" />
                        <span className="font-medium">{fm.name}</span>
                        {list.length > 0 && (
                          <span className="text-xs text-muted-foreground">
                            · {list.filter((r) => selectedByFieldId[r.id]).length}/{list.length}
                          </span>
                        )}
                      </span>
                      {isOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
                    </button>
                    {isOpen && (
                      <div className="space-y-1.5 border-t bg-muted/20 p-2">
                        {list.length === 0 && (
                          <p className="text-center text-xs text-muted-foreground">No fields on this farm</p>
                        )}
                        {list.map((f) => (
                          <FieldRowCard
                            key={f.id}
                            field={f}
                            selected={!!selectedByFieldId[f.id]}
                            block={selectedByFieldId[f.id]}
                            onToggle={(v) => toggle(f, v)}
                            onUpdate={(p) => updateBlock(f.id, p)}
                            expanded={expanded === f.id}
                            onExpand={() => setExpanded(expanded === f.id ? null : f.id)}
                            crops={crops}
                            analyses={analyses.filter((a) => !a.field_id || a.field_id === f.id)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Custom block (no field backing — rare case) */}
      <div className="border-t pt-3">
        <Button variant="outline" size="sm" onClick={addCustomBlock}>
          <Plus className="size-3.5" />
          Add custom block (no field)
        </Button>
      </div>
    </div>
  );
}

function rowToBlock(field: FieldRow): Omit<Block, "id"> {
  return {
    field_id: field.id,
    name: field.name,
    area_ha: field.size_ha,
    crop: field.crop || "",
    cultivar: field.cultivar || "",
    yield_target: field.yield_target,
    yield_unit: field.yield_unit || "",
    tree_age: field.tree_age,
    pop_per_ha: field.pop_per_ha,
    soil_analysis_id: field.latest_analysis_id || null,
    notes: "",
  };
}

interface FieldRowCardProps {
  field: FieldRow;
  selected: boolean;
  block: Omit<Block, "id"> | undefined;
  onToggle: (v: boolean) => void;
  onUpdate: (p: Partial<Block>) => void;
  expanded: boolean;
  onExpand: () => void;
  crops: CropNorm[];
  analyses: SoilAnalysis[];
}

function FieldRowCard({
  field, selected, block, onToggle, onUpdate, expanded, onExpand, crops, analyses,
}: FieldRowCardProps) {
  const crop = block?.crop || "";
  // Build a CheckableBlock off the selected wizard block. If crop is
  // set, pass its crop_type through so perennial-only checks fire
  // (tree_age, pop_per_ha).
  const cropType = crops.find((c) => c.crop === crop)?.crop_type ?? null;
  const completeness = block
    ? blockCompleteness({
        name: block.name,
        crop: block.crop,
        area_ha: block.area_ha,
        yield_target: block.yield_target,
        yield_unit: block.yield_unit,
        tree_age: block.tree_age,
        pop_per_ha: block.pop_per_ha,
        soil_analysis_id: block.soil_analysis_id,
        crop_type: cropType,
      })
    : null;

  return (
    <Card className={selected ? "border-[var(--sapling-orange)]/40" : "bg-white"}>
      <CardContent className="py-2.5 px-3">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => onToggle(e.target.checked)}
            className="size-4 shrink-0 accent-[var(--sapling-orange)]"
          />
          <div className="flex flex-1 min-w-0 items-center gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="truncate font-medium text-sm">{field.name}</span>
                {field.size_ha != null && (
                  <span className="shrink-0 text-xs text-muted-foreground">
                    · {field.size_ha} ha
                  </span>
                )}
                {selected && completeness && (
                  completeness.complete ? (
                    <span className="flex shrink-0 items-center gap-0.5 rounded-full bg-green-50 px-1.5 py-0.5 text-[10px] font-medium text-green-700">
                      <CheckCircle2 className="size-2.5" />
                      {completeness.softIssues.length === 0
                        ? "ready"
                        : `ready · ${completeness.softIssues.length} soft`}
                    </span>
                  ) : (
                    <span
                      className="flex shrink-0 items-center gap-0.5 rounded-full bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700"
                      title={completeness.hardIssues.map((i) => i.label).join(", ")}
                    >
                      <AlertCircle className="size-2.5" />
                      needs: {completeness.hardIssues.map((i) => i.label.toLowerCase()).join(", ")}
                    </span>
                  )
                )}
              </div>
              {selected && (
                <div className="mt-1 flex flex-wrap items-center gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <Leaf className="size-3 text-muted-foreground" />
                    <div className="w-36">
                      <ComboBox
                        label=""
                        placeholder="Select crop..."
                        items={crops.map((c) => ({ name: c.crop, value: c.crop }))}
                        value={crop}
                        onChange={(val) => onUpdate({ crop: val })}
                        onSelect={(item) => {
                          const c = crops.find((cr) => cr.crop === (item.value as string));
                          onUpdate({ crop: item.value as string, yield_unit: c?.yield_unit || "" });
                        }}
                      />
                    </div>
                  </div>
                  <select
                    value={block?.soil_analysis_id || ""}
                    onChange={(e) => onUpdate({ soil_analysis_id: e.target.value || null })}
                    className="rounded border bg-white px-2 py-1 text-xs"
                  >
                    <option value="">No analysis linked</option>
                    {analyses.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.crop || "?"} · {new Date(a.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            {selected && (
              <Button variant="ghost" size="sm" onClick={onExpand} className="h-6 px-2 text-xs">
                {expanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                Details
              </Button>
            )}
          </div>
        </div>

        {selected && expanded && (
          <div className="mt-3 grid gap-2 border-t pt-3 sm:grid-cols-3">
            <div className="space-y-1">
              <Label className="text-xs">Cultivar</Label>
              <Input
                className="h-8 text-sm"
                value={block?.cultivar || ""}
                onChange={(e) => onUpdate({ cultivar: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Yield target {block?.yield_unit ? `(${block.yield_unit})` : ""}</Label>
              <Input
                className="h-8 text-sm"
                type="number"
                value={block?.yield_target ?? ""}
                onChange={(e) => onUpdate({ yield_target: e.target.value ? parseFloat(e.target.value) : null })}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Tree age (perennials)</Label>
              <Input
                className="h-8 text-sm"
                type="number"
                value={block?.tree_age ?? ""}
                onChange={(e) => onUpdate({ tree_age: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
