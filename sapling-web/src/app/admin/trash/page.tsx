"use client";

import { useEffect, useState } from "react";
import { Loader2, RotateCcw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

interface DeletedRow {
  id: string;
  _type: string;
  _table: string;
  _name: string;
  _detail: string;
  deleted_at: string;
  deleted_by?: string | null;
}

interface DeletedListResponse {
  items: DeletedRow[];
  total: number;
}

const RECORD_KINDS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "blend", label: "Blends" },
  { value: "soil_analysis", label: "Soil analyses" },
  { value: "leaf_analysis", label: "Leaf analyses" },
  { value: "client", label: "Clients" },
  { value: "farm", label: "Farms" },
  { value: "field", label: "Fields" },
  { value: "yield_record", label: "Yields" },
  { value: "field_application", label: "Applications" },
  { value: "field_event", label: "Events" },
  { value: "field_crop_history", label: "Crop history" },
];

export default function AdminTrashPage() {
  const [filter, setFilter] = useState<string>("");
  const [items, setItems] = useState<DeletedRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  async function load(kind: string) {
    setLoading(true);
    try {
      const res = await api.get<DeletedListResponse>(
        `/api/admin/deleted?limit=200${kind ? `&record_type=${kind}` : ""}`,
      );
      setItems(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(filter);
  }, [filter]);

  async function restore(row: DeletedRow) {
    setBusy(row.id);
    try {
      await api.post(`/api/admin/deleted/${row._type}/${row.id}/restore`);
      toast.success(`Restored ${row._name}`);
      await load(filter);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Restore failed");
    } finally {
      setBusy(null);
    }
  }

  async function purge(row: DeletedRow) {
    if (!confirm(`Permanently delete ${row._name}? This can't be undone.`)) return;
    setBusy(row.id);
    try {
      await api.delete(`/api/admin/deleted/${row._type}/${row.id}`);
      toast.success("Permanently deleted");
      await load(filter);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Hard-delete failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Soft-deleted recovery</h1>
        <p className="text-sm text-muted-foreground">
          {total} tombstoned {total === 1 ? "record" : "records"}. Admin-only — restore brings the
          row back into agent-facing lists; permanent delete is irreversible.
        </p>
      </div>

      <div className="flex flex-wrap gap-1">
        {RECORD_KINDS.map((k) => (
          <button
            key={k.value || "all"}
            onClick={() => setFilter(k.value)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              filter === k.value
                ? "border-[var(--sapling-orange)] bg-orange-50 text-[var(--sapling-orange)]"
                : "border-gray-200 text-muted-foreground hover:bg-gray-50"
            }`}
          >
            {k.label}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="py-3">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
            </div>
          ) : items.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              Nothing in the trash for this filter.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Type</th>
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Detail</th>
                    <th className="pb-2 pr-4 font-medium">Deleted</th>
                    <th className="pb-2 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr key={`${row._type}-${row.id}`} className="border-b last:border-0">
                      <td className="py-2.5 pr-4">
                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-600">
                          {row._type.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-2.5 pr-4 font-medium text-[var(--sapling-dark)]">
                        {row._name}
                      </td>
                      <td className="py-2.5 pr-4 text-muted-foreground">{row._detail || "—"}</td>
                      <td className="py-2.5 pr-4 text-xs text-muted-foreground tabular-nums">
                        {row.deleted_at
                          ? new Date(row.deleted_at).toLocaleString(undefined, {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "—"}
                      </td>
                      <td className="py-2.5 text-right">
                        <div className="inline-flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy === row.id}
                            onClick={() => restore(row)}
                          >
                            {busy === row.id ? (
                              <Loader2 className="size-3 animate-spin" />
                            ) : (
                              <RotateCcw className="size-3" />
                            )}
                            Restore
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={busy === row.id}
                            onClick={() => purge(row)}
                            className="text-red-500 hover:bg-red-50 hover:text-red-700"
                          >
                            <Trash2 className="size-3" />
                            Purge
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
