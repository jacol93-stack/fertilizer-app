"use client";

import { useState, useEffect, useMemo, useRef } from "react";
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

      {/* Other farms on this client. The parent passes the full
          client-farm list including the active farm, so filter that
          one out first; only render the section when at least one
          *other* farm survives — otherwise the header is orphaned. */}
      {(() => {
        const visibleOtherFarms = otherFarms.filter((fm) => fm.id !== farmId);
        if (visibleOtherFarms.length === 0) return null;
        return (
        <div className={fields.length > 0 ? "border-t pt-4" : ""}>
          <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            {fields.length > 0
              ? "Other farms on this client"
              : "Farms on this client"}
          </p>
          <div className="space-y-2">
            {visibleOtherFarms
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
        );
      })()}

      {/* Custom block (no field backing — rare case) */}
      <div className="border-t pt-3 space-y-1">
        <Button
          variant="outline"
          size="sm"
          onClick={addCustomBlock}
          title="Plan for a block that isn't yet in your client database — handy for quick quotes or new fields you haven't entered yet. The block won't be linked to a saved field record."
        >
          <Plus className="size-3.5" />
          Add custom block (no field)
        </Button>
        <p className="text-[10px] text-muted-foreground">
          For one-off blocks not yet in your client&apos;s field list.
        </p>
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

// Wizard fields that mirror the field record (single source of truth for
// physical / cultivar attributes). Edits to these fan out to a debounced
// PATCH on the field row, so corrections made during the build are visible
// next time. yield_target stays programme-scoped — it varies per season.
const FIELD_WRITEBACK_KEYS = new Set([
  "cultivar", "tree_age", "pop_per_ha", "area_ha", "crop", "soil_analysis_id",
]);

// Wizard block keys → field record column names (most match, area_ha differs).
const FIELD_COLUMN_FOR_BLOCK_KEY: Record<string, string> = {
  area_ha: "size_ha",
  soil_analysis_id: "latest_analysis_id",
};

function pickWritebackPayload(patch: Partial<Block>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(patch)) {
    if (!FIELD_WRITEBACK_KEYS.has(k)) continue;
    const col = FIELD_COLUMN_FOR_BLOCK_KEY[k] ?? k;
    out[col] = v;
  }
  return out;
}

type WritebackStatus = "idle" | "saving" | "saved" | "error";

function FieldRowCard({
  field, selected, block, onToggle, onUpdate, expanded, onExpand, crops, analyses,
}: FieldRowCardProps) {
  const crop = block?.crop || "";

  // Debounced writeback — last-write-wins. Multiple keystrokes within the
  // window collapse into one PATCH carrying the latest values.
  const pendingRef = useRef<Record<string, unknown>>({});
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [writebackStatus, setWritebackStatus] = useState<WritebackStatus>("idle");
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Intercept block updates: always update local state via onUpdate;
  // additionally PATCH the field record for writeback keys (debounced).
  const handleUpdate = (patch: Partial<Block>) => {
    onUpdate(patch);
    const writeback = pickWritebackPayload(patch);
    if (Object.keys(writeback).length === 0 || !field.id) return;
    pendingRef.current = { ...pendingRef.current, ...writeback };
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      const payload = pendingRef.current;
      pendingRef.current = {};
      timerRef.current = null;
      setWritebackStatus("saving");
      try {
        await api.patch(`/api/clients/fields/${field.id}`, payload);
        setWritebackStatus("saved");
        if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
        savedTimerRef.current = setTimeout(() => setWritebackStatus("idle"), 1500);
      } catch (err) {
        console.error("Field writeback failed", err);
        setWritebackStatus("error");
        toast.error("Saved to programme but couldn't update field record");
      }
    }, 600);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
    };
  }, []);

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
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <Leaf className="size-3" />
                    <span>Crop</span>
                    {field.crop ? (
                      // Crop already set on the field record — show as
                      // static text. Edit happens upstream via the field
                      // drawer (single source of truth for field data).
                      <span className="font-medium text-[var(--sapling-dark)]">
                        {field.crop}
                        {field.cultivar ? ` · ${field.cultivar}` : ""}
                      </span>
                    ) : (
                      // Field has no crop — let the user pick one inline
                      // (rare, but happens for incomplete field records).
                      <div className="w-36">
                        <ComboBox
                          label=""
                          placeholder="Select crop..."
                          items={crops.map((c) => ({ name: c.crop, value: c.crop }))}
                          value={crop}
                          onChange={(val) => handleUpdate({ crop: val })}
                          onSelect={(item) => {
                            const c = crops.find((cr) => cr.crop === (item.value as string));
                            handleUpdate({ crop: item.value as string, yield_unit: c?.yield_unit || "" });
                          }}
                        />
                      </div>
                    )}
                  </span>
                  <label className="flex items-center gap-1.5 text-muted-foreground">
                    <span>Soil analysis</span>
                    <select
                      value={block?.soil_analysis_id || ""}
                      onChange={(e) => handleUpdate({ soil_analysis_id: e.target.value || null })}
                      className="rounded border bg-white px-2 py-1 text-xs text-[var(--sapling-dark)]"
                    >
                      <option value="">No analysis linked</option>
                      {analyses.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.lab_name ? `${a.lab_name} · ` : ""}{new Date(a.created_at).toLocaleDateString()}
                          {a.crop ? ` · ${a.crop}` : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              )}
            </div>
            {selected && writebackStatus !== "idle" && (
              <span
                className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                  writebackStatus === "saved"
                    ? "bg-green-50 text-green-700"
                    : writebackStatus === "error"
                      ? "bg-red-50 text-red-700"
                      : "bg-gray-100 text-gray-600"
                }`}
                title="Edits to cultivar / tree age / crop / soil analysis sync to the field record. Yield target is programme-scoped only."
              >
                {writebackStatus === "saving" && "saving…"}
                {writebackStatus === "saved" && "saved to field"}
                {writebackStatus === "error" && "field save failed"}
              </span>
            )}
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
                onChange={(e) => handleUpdate({ cultivar: e.target.value })}
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
                onChange={(e) => handleUpdate({ tree_age: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
