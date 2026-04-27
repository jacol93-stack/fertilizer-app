"use client";

import { useState } from "react";
import { Loader2, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function LogYieldForm({
  fieldId,
  defaultUnit,
  onSaved,
  onCancel,
}: {
  fieldId: string;
  defaultUnit: string;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [season, setSeason] = useState(() => {
    const y = new Date().getFullYear();
    return `${y}/${y + 1}`;
  });
  const [yieldActual, setYieldActual] = useState("");
  const [unit, setUnit] = useState(defaultUnit || "t/ha");
  const [harvestDate, setHarvestDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await api.post(`/api/clients/fields/${fieldId}/yields`, {
        season,
        yield_actual: parseFloat(yieldActual),
        yield_unit: unit,
        harvest_date: harvestDate || null,
        source: "manual",
        notes: notes || null,
      });
      toast.success("Yield logged");
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to log yield");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--sapling-dark)]">Log yield</h3>
        <button onClick={onCancel} className="text-muted-foreground hover:text-[var(--sapling-dark)]">
          <X className="size-4" />
        </button>
      </div>
      <div className="grid gap-2 sm:grid-cols-4">
        <label className="text-xs">
          <span className="block text-muted-foreground">Season</span>
          <input
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            placeholder="2026/2027"
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
        <label className="text-xs">
          <span className="block text-muted-foreground">Yield</span>
          <input
            type="number"
            step="0.01"
            value={yieldActual}
            onChange={(e) => setYieldActual(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm tabular-nums"
          />
        </label>
        <label className="text-xs">
          <span className="block text-muted-foreground">Unit</span>
          <input
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
        <label className="text-xs">
          <span className="block text-muted-foreground">Harvest date</span>
          <input
            type="date"
            value={harvestDate}
            onChange={(e) => setHarvestDate(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
      </div>
      <label className="block text-xs">
        <span className="block text-muted-foreground">Notes</span>
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
        />
      </label>
      <div className="flex justify-end gap-2 pt-1">
        <Button size="sm" variant="ghost" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={saving || !season || !yieldActual}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
          Save yield
        </Button>
      </div>
    </div>
  );
}
