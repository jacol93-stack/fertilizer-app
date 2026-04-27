"use client";

import { useState } from "react";
import { Loader2, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const NUTRIENTS = ["N", "P2O5", "K2O", "Ca", "Mg", "S"] as const;
const METHODS = ["broadcast", "fertigation", "foliar", "band_place", "side_dress"] as const;

export function LogApplicationForm({
  fieldId,
  onSaved,
  onCancel,
}: {
  fieldId: string;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [product, setProduct] = useState("");
  const [rateKg, setRateKg] = useState("");
  const [rateL, setRateL] = useState("");
  const [method, setMethod] = useState<string>("broadcast");
  const [nutrients, setNutrients] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const cleanNutrients: Record<string, number> = {};
      for (const [k, v] of Object.entries(nutrients)) {
        const n = parseFloat(v);
        if (!isNaN(n)) cleanNutrients[k] = n;
      }
      await api.post(`/api/clients/fields/${fieldId}/applications`, {
        applied_date: date,
        product_label: product || null,
        rate_kg_ha: rateKg ? parseFloat(rateKg) : null,
        rate_l_ha: rateL ? parseFloat(rateL) : null,
        method,
        nutrients_kg_per_ha: Object.keys(cleanNutrients).length > 0 ? cleanNutrients : null,
        notes: notes || null,
      });
      toast.success("Application logged");
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to log application");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--sapling-dark)]">Log application</h3>
        <button onClick={onCancel} className="text-muted-foreground hover:text-[var(--sapling-dark)]">
          <X className="size-4" />
        </button>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <label className="text-xs">
          <span className="block text-muted-foreground">Date</span>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
        <label className="text-xs sm:col-span-2">
          <span className="block text-muted-foreground">Product / blend</span>
          <input
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            placeholder='e.g. "5:1:5 (17) + Ca 4.1%" or "Calcitic Lime"'
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        <label className="text-xs">
          <span className="block text-muted-foreground">Method</span>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          >
            {METHODS.map((m) => (
              <option key={m} value={m}>
                {m.replace("_", "-")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs">
          <span className="block text-muted-foreground">Rate (kg/ha)</span>
          <input
            type="number"
            step="0.1"
            value={rateKg}
            onChange={(e) => setRateKg(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
        <label className="text-xs">
          <span className="block text-muted-foreground">Rate (L/ha)</span>
          <input
            type="number"
            step="0.1"
            value={rateL}
            onChange={(e) => setRateL(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          />
        </label>
      </div>

      <div>
        <p className="mb-1 text-xs text-muted-foreground">
          Nutrients delivered per ha (kg) — leave blank if unknown
        </p>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          {NUTRIENTS.map((n) => (
            <label key={n} className="text-xs">
              <span className="block text-[10px] uppercase tracking-wide text-muted-foreground">
                {n}
              </span>
              <input
                type="number"
                step="0.1"
                value={nutrients[n] ?? ""}
                onChange={(e) =>
                  setNutrients((prev) => ({ ...prev, [n]: e.target.value }))
                }
                className="mt-0.5 h-7 w-full rounded border bg-white px-1.5 text-sm tabular-nums"
              />
            </label>
          ))}
        </div>
      </div>

      <label className="block text-xs">
        <span className="block text-muted-foreground">Notes</span>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional context — weather, equipment, etc."
          rows={2}
          className="mt-0.5 w-full rounded border bg-white px-2 py-1 text-sm"
        />
      </label>

      <div className="flex justify-end gap-2 pt-1">
        <Button size="sm" variant="ghost" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={saving || !date}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
          Save application
        </Button>
      </div>
    </div>
  );
}
