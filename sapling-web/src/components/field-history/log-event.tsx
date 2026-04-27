"use client";

import { useState } from "react";
import { Loader2, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const EVENT_TYPES: Array<{ value: string; label: string }> = [
  { value: "cultivar_change", label: "Cultivar change / top-work" },
  { value: "replant", label: "Replant" },
  { value: "pruning", label: "Pruning" },
  { value: "rootstock_change", label: "Rootstock change" },
  { value: "frost", label: "Frost damage" },
  { value: "hail", label: "Hail damage" },
  { value: "drought_stress", label: "Drought stress" },
  { value: "irrigation_change", label: "Irrigation change" },
  { value: "other", label: "Other" },
];

export function LogEventForm({
  fieldId,
  onSaved,
  onCancel,
}: {
  fieldId: string;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [eventType, setEventType] = useState("cultivar_change");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await api.post(`/api/clients/fields/${fieldId}/events`, {
        event_date: date,
        event_type: eventType,
        title,
        description: description || null,
      });
      toast.success("Event logged");
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to log event");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--sapling-dark)]">Log event</h3>
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
          <span className="block text-muted-foreground">Type</span>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
          >
            {EVENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>
      </div>
      <label className="block text-xs">
        <span className="block text-muted-foreground">Headline</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder='e.g. "Top-worked Hass → Lamb Hass" or "Frost Aug 12 — 15% bud loss"'
          className="mt-0.5 h-8 w-full rounded border bg-white px-2 text-sm"
        />
      </label>
      <label className="block text-xs">
        <span className="block text-muted-foreground">Description</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
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
          disabled={saving || !title}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
          Save event
        </Button>
      </div>
    </div>
  );
}
