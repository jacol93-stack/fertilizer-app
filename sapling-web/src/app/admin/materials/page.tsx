"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, X, Save, Loader2, Check } from "lucide-react";

interface Material {
  id: number;
  material: string;
  type: string | null;
  cost_per_ton: number;
  n: number;
  p: number;
  k: number;
  ca: number;
  mg: number;
  s: number;
  fe: number;
  b: number;
  mn: number;
  zn: number;
  mo: number;
  cu: number;
  c: number;
}

const NUTRIENT_FIELDS = [
  "n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu", "c",
] as const;

const emptyMaterial: Omit<Material, "id"> = {
  material: "",
  type: null,
  cost_per_ton: 0,
  n: 0, p: 0, k: 0, ca: 0, mg: 0, s: 0,
  fe: 0, b: 0, mn: 0, zn: 0, mo: 0, cu: 0, c: 0,
};

export default function MaterialsPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState<Material | null>(null);
  const [form, setForm] = useState<Omit<Material, "id">>(emptyMaterial);
  const [saving, setSaving] = useState(false);

  // Delete confirm
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Defaults section
  const [defaultMats, setDefaultMats] = useState<Set<string>>(new Set());
  const [defaultMinCompost, setDefaultMinCompost] = useState(50);
  const [defaultsLoading, setDefaultsLoading] = useState(true);
  const [defaultsSaving, setDefaultsSaving] = useState(false);
  const [defaultsExpanded, setDefaultsExpanded] = useState(false);

  // Liquid defaults section
  const [liquidDefaultMats, setLiquidDefaultMats] = useState<Set<string>>(new Set());
  const [liquidDefaultsExpanded, setLiquidDefaultsExpanded] = useState(false);
  const [liquidDefaultsSaving, setLiquidDefaultsSaving] = useState(false);
  const [liquidMaterials, setLiquidMaterials] = useState<Material[]>([]);

  const fetchDefaults = useCallback(async () => {
    try {
      const d = await api.get<{ materials: string[]; liquid_materials: string[]; agent_min_compost_pct: number }>("/api/materials/defaults");
      setDefaultMats(new Set(d.materials));
      setLiquidDefaultMats(new Set(d.liquid_materials || []));
      setDefaultMinCompost(d.agent_min_compost_pct ?? 50);
    } catch {} finally {
      setDefaultsLoading(false);
    }
  }, []);

  // Load liquid-compatible materials for the liquid defaults section
  const fetchLiquidMaterials = useCallback(async () => {
    try {
      const data = await api.get<Material[]>("/api/blends/liquid-materials");
      setLiquidMaterials(data.sort((a, b) => a.material.localeCompare(b.material)));
    } catch {}
  }, []);

  async function saveDefaults() {
    setDefaultsSaving(true);
    try {
      await api.put("/api/materials/defaults", {
        materials: [...defaultMats],
        agent_min_compost_pct: defaultMinCompost,
      });
      toast.success("Default materials updated for all agents");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setDefaultsSaving(false);
    }
  }

  async function saveLiquidDefaults() {
    setLiquidDefaultsSaving(true);
    try {
      await api.put("/api/materials/defaults", {
        liquid_materials: [...liquidDefaultMats],
      });
      toast.success("Liquid default materials updated for all agents");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setLiquidDefaultsSaving(false);
    }
  }

  const fetchMaterials = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.get<Material[]>("/api/materials");
      setMaterials(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load materials");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace("/");
      return;
    }
    if (!authLoading && isAdmin) {
      fetchMaterials();
      fetchDefaults();
      fetchLiquidMaterials();
    }
  }, [authLoading, isAdmin, router, fetchMaterials, fetchDefaults, fetchLiquidMaterials]);

  function openAdd() {
    setEditingMaterial(null);
    setForm({ ...emptyMaterial });
    setDialogOpen(true);
  }

  function openEdit(mat: Material) {
    setEditingMaterial(mat);
    const { id, ...rest } = mat;
    setForm(rest);
    setDialogOpen(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editingMaterial) {
        await api.patch(`/api/materials/${editingMaterial.id}`, form);
        toast.success("Material updated");
      } else {
        await api.post("/api/materials", form);
        toast.success("Material created");
      }
      setDialogOpen(false);
      fetchMaterials();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await api.delete(`/api/materials/${deleteId}`);
      toast.success("Material deleted");
      setDeleteId(null);
      fetchMaterials();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  function updateForm(field: string, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  if (authLoading) return null;

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Materials</h1>
            <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
              Manage fertilizer materials and nutrient compositions
            </p>
          </div>
          <Button onClick={openAdd}>
            <Plus className="size-4" data-icon="inline-start" />
            Add Material
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* ── Default Materials for Agents ── */}
        <Card className="mt-6">
          <CardHeader className="cursor-pointer" onClick={() => setDefaultsExpanded(!defaultsExpanded)}>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Agent Default Materials</CardTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {defaultMats.size} materials selected &middot; {defaultMinCompost}% min compost &middot; These are pre-selected for all agents on Quick Blend
                </p>
              </div>
              <span className="text-xs text-muted-foreground">{defaultsExpanded ? "Collapse" : "Expand"}</span>
            </div>
          </CardHeader>
          {defaultsExpanded && (
            <CardContent className="space-y-4">
              {defaultsLoading ? (
                <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
              ) : (
                <>
                  <div className="max-h-64 space-y-1 overflow-y-auto rounded-lg border p-2">
                    {materials
                      .filter((m) => m.material !== "Manure Compost" && m.material !== "Dolomitic Lime (Filler)")
                      .map((mat) => (
                      <label
                        key={mat.id || mat.material}
                        className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1 transition-colors hover:bg-muted"
                      >
                        <input
                          type="checkbox"
                          checked={defaultMats.has(mat.material)}
                          onChange={() => {
                            setDefaultMats((prev) => {
                              const next = new Set(prev);
                              if (next.has(mat.material)) next.delete(mat.material);
                              else next.add(mat.material);
                              return next;
                            });
                          }}
                          className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                        />
                        <span className="flex-1 text-sm">{mat.material}</span>
                        {mat.type && <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">{mat.type}</span>}
                      </label>
                    ))}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Label className="text-xs whitespace-nowrap">Min Compost %</Label>
                      <Input
                        type="number"
                        className="w-20"
                        value={defaultMinCompost}
                        onChange={(e) => setDefaultMinCompost(parseInt(e.target.value) || 0)}
                        min={0}
                        max={100}
                      />
                    </div>
                    <div className="flex gap-2 ml-auto">
                      <button
                        type="button"
                        onClick={() => setDefaultMats(new Set(materials.filter((m) => m.material !== "Manure Compost" && m.material !== "Dolomitic Lime (Filler)").map((m) => m.material)))}
                        className="text-xs text-[var(--sapling-orange)] hover:underline"
                      >
                        Select all
                      </button>
                      <button
                        type="button"
                        onClick={() => setDefaultMats(new Set())}
                        className="text-xs text-muted-foreground hover:underline"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                  <Button onClick={saveDefaults} disabled={defaultsSaving} className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90">
                    {defaultsSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                    Save Defaults
                  </Button>
                </>
              )}
            </CardContent>
          )}
        </Card>

        {/* ── Liquid Default Materials for Agents ── */}
        <Card className="mt-4">
          <CardHeader className="cursor-pointer" onClick={() => setLiquidDefaultsExpanded(!liquidDefaultsExpanded)}>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Agent Default Liquid Materials</CardTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {liquidDefaultMats.size} materials selected &middot; Pre-selected for agents on Liquid Blend
                </p>
              </div>
              <span className="text-xs text-muted-foreground">{liquidDefaultsExpanded ? "Collapse" : "Expand"}</span>
            </div>
          </CardHeader>
          {liquidDefaultsExpanded && (
            <CardContent className="space-y-4">
              {defaultsLoading ? (
                <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
              ) : (
                <>
                  <div className="max-h-64 space-y-1 overflow-y-auto rounded-lg border p-2">
                    {liquidMaterials.map((mat) => (
                      <label
                        key={mat.id || mat.material}
                        className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1 transition-colors hover:bg-muted"
                      >
                        <input
                          type="checkbox"
                          checked={liquidDefaultMats.has(mat.material)}
                          onChange={() => {
                            setLiquidDefaultMats((prev) => {
                              const next = new Set(prev);
                              if (next.has(mat.material)) next.delete(mat.material);
                              else next.add(mat.material);
                              return next;
                            });
                          }}
                          className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                        />
                        <span className="flex-1 text-sm">{mat.material}</span>
                        {mat.type && <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">{mat.type}</span>}
                      </label>
                    ))}
                    {liquidMaterials.length === 0 && (
                      <p className="py-4 text-center text-sm text-muted-foreground">
                        No liquid-compatible materials found. Mark materials as liquid-compatible in the table below.
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2 ml-auto">
                    <button
                      type="button"
                      onClick={() => setLiquidDefaultMats(new Set(liquidMaterials.map((m) => m.material)))}
                      className="text-xs text-[var(--sapling-orange)] hover:underline"
                    >
                      Select all
                    </button>
                    <button
                      type="button"
                      onClick={() => setLiquidDefaultMats(new Set())}
                      className="text-xs text-muted-foreground hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                  <Button onClick={saveLiquidDefaults} disabled={liquidDefaultsSaving} className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90">
                    {liquidDefaultsSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                    Save Liquid Defaults
                  </Button>
                </>
              )}
            </CardContent>
          )}
        </Card>

        {loading ? (
          <div className="mt-8 flex justify-center">
            <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-[var(--sapling-orange)]" />
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3 text-right">Cost/ton</th>
                  <th className="px-4 py-3 text-right">N%</th>
                  <th className="px-4 py-3 text-right">P%</th>
                  <th className="px-4 py-3 text-right">K%</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {materials.map((mat) => (
                  <tr
                    key={mat.id || mat.material}
                    className="cursor-pointer transition-colors hover:bg-gray-50"
                    onClick={() => openEdit(mat)}
                  >
                    <td className="px-4 py-3 font-medium text-[var(--sapling-dark)]">
                      {mat.material}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{mat.type ?? "-"}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      R{mat.cost_per_ton.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{mat.n}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{mat.p}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{mat.k}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            openEdit(mat);
                          }}
                        >
                          <Pencil className="size-3.5" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteId(mat.id);
                          }}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {materials.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                      No materials found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
                {editingMaterial ? "Edit Material" : "Add Material"}
              </h2>
              <Button variant="ghost" size="icon-xs" onClick={() => setDialogOpen(false)}>
                <X className="size-4" />
              </Button>
            </div>

            <div className="mt-4 grid gap-4">
              <div className="grid gap-1.5">
                <Label htmlFor="material">Name</Label>
                <Input
                  id="material"
                  value={form.material}
                  onChange={(e) => updateForm("material", e.target.value)}
                  placeholder="e.g. Urea 46%"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="type">Type</Label>
                  <Input
                    id="type"
                    value={form.type ?? ""}
                    onChange={(e) => updateForm("type", e.target.value)}
                    placeholder="e.g. Nitrogen"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="cost_per_ton">Cost per Ton (R)</Label>
                  <Input
                    id="cost_per_ton"
                    type="number"
                    value={form.cost_per_ton}
                    onChange={(e) => updateForm("cost_per_ton", parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="border-t pt-4">
                <p className="mb-3 text-sm font-medium text-gray-700">Nutrient Composition (%)</p>
                <div className="grid grid-cols-4 gap-3">
                  {NUTRIENT_FIELDS.map((field) => (
                    <div key={field} className="grid gap-1">
                      <Label htmlFor={field} className="text-xs uppercase">
                        {field}
                      </Label>
                      <Input
                        id={field}
                        type="number"
                        step="0.01"
                        value={form[field]}
                        onChange={(e) =>
                          updateForm(field, parseFloat(e.target.value) || 0)
                        }
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving || !form.material.trim()}>
                {saving ? "Saving..." : editingMaterial ? "Update" : "Create"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
              Delete Material
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Are you sure you want to delete this material? This action cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteId(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
