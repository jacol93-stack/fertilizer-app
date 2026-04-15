"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Plus, Loader2 } from "lucide-react";
import { PRODUCT_TYPES, APPLICATION_METHODS } from "@/lib/season-constants";
import type { Block, ProgrammeApplication } from "@/lib/season-constants";

interface RecordApplicationProps {
  programmeId: string;
  blocks: Block[];
}

export function RecordApplication({ programmeId, blocks }: RecordApplicationProps) {
  const [applications, setApplications] = useState<ProgrammeApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [blockId, setBlockId] = useState(blocks[0]?.id || "");
  const [actualDate, setActualDate] = useState(new Date().toISOString().split("T")[0]);
  const [productName, setProductName] = useState("");
  const [productType, setProductType] = useState("pelletised");
  const [rateKgHa, setRateKgHa] = useState("");
  const [method, setMethod] = useState("broadcast");
  const [isSaplingProduct, setIsSaplingProduct] = useState(true);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    api.get<ProgrammeApplication[]>(`/api/programmes/${programmeId}/applications`)
      .then(setApplications)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [programmeId]);

  const handleSubmit = async () => {
    if (!blockId) { toast.error("Select a block"); return; }
    setSaving(true);
    try {
      const result = await api.post<ProgrammeApplication>(
        `/api/programmes/${programmeId}/applications`,
        {
          block_id: blockId,
          actual_date: actualDate || null,
          actual_rate_kg_ha: rateKgHa ? parseFloat(rateKgHa) : null,
          product_name: productName || null,
          product_type: productType,
          is_sapling_product: isSaplingProduct,
          method,
          notes: notes || null,
          status: "applied",
        }
      );
      setApplications((prev) => [result, ...prev]);
      toast.success("Application recorded");

      // Reset form
      setProductName("");
      setRateKgHa("");
      setNotes("");
      setIsSaplingProduct(true);
      setShowForm(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to record application");
    } finally {
      setSaving(false);
    }
  };

  const blockMap = new Map(blocks.map((b) => [b.id, b.name]));

  return (
    <div className="space-y-6">
      {/* Record form */}
      {showForm ? (
        <Card className="border-2 border-[var(--sapling-orange)]">
          <CardHeader>
            <CardTitle>Record Application</CardTitle>
            <CardDescription>Log a fertilizer application that was made</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Block</Label>
                <select
                  value={blockId}
                  onChange={(e) => setBlockId(e.target.value)}
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                >
                  {blocks.map((b) => (
                    <option key={b.id} value={b.id}>{b.name} ({b.crop})</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Date</Label>
                <Input
                  type="date"
                  value={actualDate}
                  onChange={(e) => setActualDate(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Product Name</Label>
                <Input
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g. Sapling 3:2:1"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Product Type</Label>
                <select
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                >
                  {PRODUCT_TYPES.map((t) => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Rate (kg/ha)</Label>
                <Input
                  type="number"
                  value={rateKgHa}
                  onChange={(e) => setRateKgHa(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Method</Label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  className="w-full rounded-md border bg-white px-3 py-2 text-sm"
                >
                  {APPLICATION_METHODS.map((m) => (
                    <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isSaplingProduct}
                  onChange={(e) => setIsSaplingProduct(e.target.checked)}
                  className="size-4 rounded border-gray-300"
                />
                Sapling product
              </label>
              {!isSaplingProduct && (
                <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                  Competitor
                </span>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes"
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleSubmit}
                disabled={saving}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {saving ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                Record Application
              </Button>
              <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Button
          onClick={() => setShowForm(true)}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <Plus className="size-4" />
          Record Application
        </Button>
      )}

      {/* Application history */}
      <Card>
        <CardHeader>
          <CardTitle>Application History</CardTitle>
          <CardDescription>{applications.length} application{applications.length !== 1 ? "s" : ""} recorded</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : applications.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No applications recorded yet
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Date</th>
                    <th className="pb-2 pr-3 font-medium">Block</th>
                    <th className="pb-2 pr-3 font-medium">Product</th>
                    <th className="pb-2 pr-3 font-medium">Type</th>
                    <th className="pb-2 pr-3 font-medium">Rate</th>
                    <th className="pb-2 pr-3 font-medium">Method</th>
                    <th className="pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {applications.map((app) => (
                    <tr key={app.id} className="border-b last:border-0">
                      <td className="py-2 pr-3">
                        {app.actual_date ? new Date(app.actual_date).toLocaleDateString() : "—"}
                      </td>
                      <td className="py-2 pr-3">{blockMap.get(app.block_id) || "—"}</td>
                      <td className="py-2 pr-3">
                        <div className="flex items-center gap-1.5">
                          {app.product_name || "—"}
                          {!app.is_sapling_product && (
                            <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700">
                              Competitor
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-2 pr-3 capitalize">{app.product_type || "—"}</td>
                      <td className="py-2 pr-3 tabular-nums">{app.actual_rate_kg_ha ?? "—"}</td>
                      <td className="py-2 pr-3 capitalize">{app.method || "—"}</td>
                      <td className="py-2">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          app.status === "applied" ? "bg-green-100 text-green-700"
                          : app.status === "pending" ? "bg-amber-100 text-amber-700"
                          : app.status === "skipped" ? "bg-gray-100 text-gray-500"
                          : "bg-blue-100 text-blue-700"
                        }`}>
                          {app.status}
                        </span>
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
