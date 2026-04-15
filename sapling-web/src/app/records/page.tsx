"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  FileText,
  Search,
  Download,
  Trash2,
  Loader2,
  FlaskConical,
  Leaf,
  Calendar,
  X,
  AlertTriangle,
  Eye,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Droplets,
} from "lucide-react";
import { useRecordPreview, RecordPreviewSheet } from "@/components/record-preview-sheet";
import { useEffectiveAdmin } from "@/lib/use-effective-role";

// ── Types ──────────────────────────────────────────────────────────────────

interface BlendRecord {
  id: string;
  blend_name: string | null;
  blend_type: string | null;
  client_name: string | null;
  farm_name: string | null;
  cost_per_ton: number | null;
  created_at: string;
  [key: string]: unknown;
}

interface SoilRecord {
  id: string;
  crop: string | null;
  cultivar: string | null;
  lab_name: string | null;
  total_cost_ha: number | null;
  created_at: string;
  [key: string]: unknown;
}

interface DeletedRecord {
  id: string;
  _type: "blend" | "soil_analysis";
  _name: string;
  _detail: string;
  deleted_at: string;
  deleted_by: string;
  agent_id: string;
  created_by: string;
  [key: string]: unknown;
}

interface ProfileEntry {
  id: string;
  full_name: string | null;
  username: string | null;
  [key: string]: unknown;
}

interface AdminUser {
  id: string;
  name: string;
  email: string;
}

// ── Confirm Dialog ─────────────────────────────────────────────────────────

function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  loading: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="size-5" />
          </button>
        </div>
        <p className="mb-4 text-sm text-muted-foreground">{message}</p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading && <Loader2 className="size-4 animate-spin" />}
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Expanded Deleted Record Views ──────────────────────────────────────────

function ExpandedBlendView({ record, isAdmin }: { record: DeletedRecord; isAdmin: boolean }) {
  const r = record as Record<string, unknown>;
  const recipe = r.recipe as Record<string, unknown>[] | undefined;
  const nutrients = r.nutrients as Record<string, unknown> | undefined;
  const targets = r.targets as Record<string, unknown> | undefined;

  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-x-8 gap-y-1 sm:grid-cols-3">
        <div><span className="font-medium text-muted-foreground">Blend Name:</span> {String(r.blend_name || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Client:</span> {String(r.client_name || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Farm:</span> {String(r.farm_name || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Batch Size:</span> {r.batch_size ? `${r.batch_size} tons` : "-"}</div>
        {isAdmin && <div><span className="font-medium text-muted-foreground">Cost/Ton:</span> {r.cost_per_ton ? `R${Number(r.cost_per_ton).toFixed(0)}` : "-"}</div>}
      </div>

      {targets && Object.keys(targets).length > 0 && (
        <div>
          <h4 className="mb-1 font-medium text-muted-foreground">Targets</h4>
          <div className="grid grid-cols-3 gap-x-6 gap-y-0.5 sm:grid-cols-4">
            {Object.entries(targets).map(([key, val]) => (
              <div key={key}><span className="text-muted-foreground">{key}:</span> {String(val ?? "-")}</div>
            ))}
          </div>
        </div>
      )}

      {recipe && recipe.length > 0 && (
        <div>
          <h4 className="mb-1 font-medium text-muted-foreground">Recipe</h4>
          <table className="w-full max-w-lg text-xs">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                {Object.keys(recipe[0]).map((col) => (
                  <th key={col} className="pb-1 pr-3 font-medium">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recipe.map((row, i) => (
                <tr key={i} className="border-b last:border-0">
                  {Object.values(row).map((val, j) => (
                    <td key={j} className="py-0.5 pr-3">{String(val ?? "-")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {nutrients && Object.keys(nutrients).length > 0 && (
        <div>
          <h4 className="mb-1 font-medium text-muted-foreground">Nutrients</h4>
          <div className="grid grid-cols-3 gap-x-6 gap-y-0.5 sm:grid-cols-4">
            {Object.entries(nutrients).map(([key, val]) => (
              <div key={key}><span className="text-muted-foreground">{key}:</span> {String(val ?? "-")}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ExpandedSoilView({ record }: { record: DeletedRecord }) {
  const r = record as Record<string, unknown>;
  const soilValues = r.soil_values as Record<string, unknown> | undefined;
  const nutrientTargets = r.nutrient_targets as Record<string, unknown> | undefined;

  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-x-8 gap-y-1 sm:grid-cols-3">
        <div><span className="font-medium text-muted-foreground">Customer:</span> {String(r.customer || r.client_name || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Farm:</span> {String(r.farm || r.farm_name || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Field:</span> {String(r.field || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Crop:</span> {String(r.crop || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Cultivar:</span> {String(r.cultivar || "-")}</div>
        <div><span className="font-medium text-muted-foreground">Yield Target:</span> {String(r.yield_target || "-")}</div>
      </div>

      {soilValues && Object.keys(soilValues).length > 0 && (
        <div>
          <h4 className="mb-1 font-medium text-muted-foreground">Soil Values</h4>
          <div className="grid grid-cols-2 gap-x-8 gap-y-0.5 sm:grid-cols-4">
            {Object.entries(soilValues).map(([key, val]) => (
              <div key={key}><span className="text-muted-foreground">{key}:</span> {String(val ?? "-")}</div>
            ))}
          </div>
        </div>
      )}

      {nutrientTargets && Object.keys(nutrientTargets).length > 0 && (
        <div>
          <h4 className="mb-1 font-medium text-muted-foreground">Nutrient Targets</h4>
          <div className="grid grid-cols-2 gap-x-8 gap-y-0.5 sm:grid-cols-4">
            {Object.entries(nutrientTargets).map(([key, val]) => (
              <div key={key}><span className="text-muted-foreground">{key}:</span> {String(val ?? "-")}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

export default function RecordsPage() {
  const { isLoading: authLoading } = useAuth();
  const isAdmin = useEffectiveAdmin();
  const [activeTab, setActiveTab] = useState<"blends" | "soil" | "deleted">("blends");
  const [search, setSearch] = useState("");
  const preview = useRecordPreview();

  // Blends
  const [blends, setBlends] = useState<BlendRecord[]>([]);
  const [blendsLoading, setBlendsLoading] = useState(true);

  // Soil
  const [soilRecords, setSoilRecords] = useState<SoilRecord[]>([]);
  const [soilLoading, setSoilLoading] = useState(true);

  // Deleted records (admin)
  const [deletedRecords, setDeletedRecords] = useState<DeletedRecord[]>([]);
  const [deletedLoading, setDeletedLoading] = useState(false);
  const [profiles, setProfiles] = useState<Record<string, string>>({});
  const [deletedTypeFilter, setDeletedTypeFilter] = useState<"all" | "blend" | "soil_analysis">("all");
  const [deletedUserFilter, setDeletedUserFilter] = useState<string>("all");
  const [permDeleteTarget, setPermDeleteTarget] = useState<{
    type: "blend" | "soil_analysis";
    id: string;
    name: string;
  } | null>(null);
  const [permDeleting, setPermDeleting] = useState(false);

  // Delete
  const [deleteTarget, setDeleteTarget] = useState<{
    type: "blend" | "soil";
    id: string;
    name: string;
  } | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Admin user filter
  const [userFilter, setUserFilter] = useState<string>("all");
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);

  // Expanded deleted record view
  const [expandedDeletedId, setExpandedDeletedId] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  // Fetch blends
  const fetchBlends = useCallback(async () => {
    setBlendsLoading(true);
    try {
      const data = await api.getAll<BlendRecord>("/api/blends");
      setBlends(data);
    } catch {
      // May not have blends endpoint yet
      setBlends([]);
    } finally {
      setBlendsLoading(false);
    }
  }, []);

  // Fetch soil records
  const fetchSoilRecords = useCallback(async () => {
    setSoilLoading(true);
    try {
      const data = await api.getAll<SoilRecord>("/api/soil");
      setSoilRecords(data);
    } catch {
      setSoilRecords([]);
    } finally {
      setSoilLoading(false);
    }
  }, []);

  // Fetch deleted records (admin only)
  const fetchDeletedRecords = useCallback(async () => {
    if (!isAdmin) return;
    setDeletedLoading(true);
    try {
      const data = await api.getAll<DeletedRecord>("/api/admin/deleted");
      setDeletedRecords(data);

      // Collect unique user IDs and resolve names
      const userIds = new Set<string>();
      for (const r of data) {
        if (r.deleted_by) userIds.add(r.deleted_by);
      }
      if (userIds.size > 0) {
        try {
          const profileList = await api.get<ProfileEntry[]>("/api/admin/profiles");
          const map: Record<string, string> = {};
          for (const p of profileList) {
            map[p.id] = p.full_name || p.username || p.id.slice(0, 8);
          }
          setProfiles(map);
        } catch {
          // Profiles endpoint may not exist; fall back to IDs
        }
      }
    } catch {
      setDeletedRecords([]);
    } finally {
      setDeletedLoading(false);
    }
  }, [isAdmin]);

  // Fetch admin user list for filter dropdown
  useEffect(() => {
    if (!isAdmin) return;
    (async () => {
      try {
        const users = await api.getAll<AdminUser>("/api/admin/users");
        setAdminUsers(users);
      } catch {
        // silently fail
      }
    })();
  }, [isAdmin]);

  useEffect(() => {
    if (authLoading) return;
    fetchBlends();
    fetchSoilRecords();
  }, [authLoading, fetchBlends, fetchSoilRecords]);

  useEffect(() => {
    if (isAdmin && activeTab === "deleted") {
      fetchDeletedRecords();
    }
  }, [isAdmin, activeTab, fetchDeletedRecords]);

  // Filter
  const filteredBlends = blends.filter((b) => {
    if (isAdmin && userFilter !== "all" && (b as Record<string, unknown>).agent_id !== userFilter) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (b.blend_name && b.blend_name.toLowerCase().includes(q)) ||
      (b.client_name && b.client_name.toLowerCase().includes(q)) ||
      (b.farm_name && b.farm_name.toLowerCase().includes(q)) ||
      (b.blend_type && b.blend_type.toLowerCase().includes(q)) ||
      (((b as Record<string, unknown>).client as string)?.toLowerCase().includes(q)) ||
      (((b as Record<string, unknown>).farm as string)?.toLowerCase().includes(q))
    );
  });

  const filteredSoil = soilRecords.filter((s) => {
    if (isAdmin && userFilter !== "all" && (s as Record<string, unknown>).agent_id !== userFilter) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (s.crop && s.crop.toLowerCase().includes(q)) ||
      (s.lab_name && s.lab_name.toLowerCase().includes(q))
    );
  });

  // Delete handler
  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      if (deleteTarget.type === "blend") {
        await api.post(`/api/blends/${deleteTarget.id}/delete`);
        setBlends((prev) => prev.filter((b) => b.id !== deleteTarget.id));
      } else {
        await api.post(`/api/soil/${deleteTarget.id}/delete`);
        setSoilRecords((prev) =>
          prev.filter((s) => s.id !== deleteTarget.id)
        );
      }
      setDeleteTarget(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  };

  // PDF download
  const [downloading, setDownloading] = useState<string | null>(null);
  const handleDownloadPdf = async (type: "blend" | "soil", id: string, name: string) => {
    if (downloading) return; // Prevent double-click
    setDownloading(id);
    try {
      const path =
        type === "blend" ? `/api/reports/blend/${id}/pdf` : `/api/reports/soil/${id}/pdf`;
      const blob = await api.getPdf(path);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${name || type}-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("PDF download failed");
    } finally {
      setDownloading(null);
    }
  };

  // Permanent delete handler (admin)
  const handlePermanentDelete = async () => {
    if (!permDeleteTarget) return;
    setPermDeleting(true);
    try {
      const apiType = permDeleteTarget.type === "blend" ? "blend" : "soil_analysis";
      await api.delete(`/api/admin/deleted/${apiType}/${permDeleteTarget.id}`);
      setDeletedRecords((prev) => prev.filter(
        (r) => !(r.id === permDeleteTarget.id && r._type === permDeleteTarget.type)
      ));
      setPermDeleteTarget(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Permanent delete failed");
    } finally {
      setPermDeleting(false);
    }
  };

  // Filtered deleted records
  const filteredDeleted = deletedRecords.filter((r) => {
    if (deletedTypeFilter !== "all" && r._type !== deletedTypeFilter) return false;
    if (deletedUserFilter !== "all" && r.deleted_by !== deletedUserFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        r._name.toLowerCase().includes(q) ||
        r._detail.toLowerCase().includes(q) ||
        (r.created_by && r.created_by.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Unique users who deleted records (for filter dropdown)
  const deletedByUsers = Array.from(
    new Map(
      deletedRecords.map((r) => [r.deleted_by, profiles[r.deleted_by] || r.deleted_by.slice(0, 8)])
    )
  );

  const blendsLabel = "Blends";
  const soilLabel = "Soil Analyses";

  const tabs = [
    { key: "blends" as const, label: blendsLabel, icon: FlaskConical },
    { key: "soil" as const, label: soilLabel, icon: Leaf },
    ...(isAdmin
      ? [{ key: "deleted" as const, label: "Deleted Records", icon: AlertTriangle }]
      : []),
  ];

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <FileText className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
              My Records
            </h1>
            <p className="text-sm text-[var(--sapling-medium-grey)]">
              View and manage your saved blends and soil analyses
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 font-medium underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-4 flex gap-1 rounded-lg bg-muted p-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key);
                setSearch("");
              }}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
              }`}
            >
              <tab.icon className="size-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Admin user filter (blends/soil tabs only) */}
        {isAdmin && (activeTab === "blends" || activeTab === "soil") && (
          <div className="mb-3">
            <select
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
            >
              <option value="all">All Users</option>
              {adminUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={
              activeTab === "blends"
                ? "Search blends by name, client, or farm..."
                : activeTab === "soil"
                  ? "Search by crop or lab name..."
                  : "Search deleted records by name or detail..."
            }
            className="pl-9"
          />
        </div>

        {/* ── Blends Tab ────────────────────────────────────────── */}
        {activeTab === "blends" && (
          <Card>
            <CardHeader>
              <CardTitle>
                {blendsLabel} ({filteredBlends.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {blendsLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
                </div>
              ) : filteredBlends.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  {search
                    ? "No blends match your search"
                    : "No saved blends yet"}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4 font-medium">Blend Name</th>
                        <th className="pb-2 pr-4 font-medium">Client</th>
                        <th className="pb-2 pr-4 font-medium">Farm</th>
                        {isAdmin && <th className="pb-2 pr-4 font-medium">Cost/Ton</th>}
                        <th className="pb-2 pr-4 font-medium">Date</th>
                        <th className="pb-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredBlends.map((blend) => (
                        <tr
                          key={blend.id}
                          onClick={() => preview.openPreview("blend", blend.id)}
                          className="cursor-pointer border-b last:border-0 hover:bg-gray-50"
                        >
                          <td className="py-2.5 pr-4 font-medium">
                            <span className="flex items-center gap-1.5">
                              {blend.blend_type === "liquid" ? (
                                <Droplets className="size-3.5 shrink-0 text-blue-500" />
                              ) : (
                                <FlaskConical className="size-3.5 shrink-0 text-[var(--sapling-orange)]" />
                              )}
                              {blend.blend_name || "Unnamed Blend"}
                              {blend.blend_type === "liquid" && (
                                <span className="rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                                  Liquid
                                </span>
                              )}
                            </span>
                          </td>
                          <td className="py-2.5 pr-4">
                            {blend.client_name || (blend as Record<string, unknown>).client as string || "-"}
                          </td>
                          <td className="py-2.5 pr-4">
                            {blend.farm_name || (blend as Record<string, unknown>).farm as string || "-"}
                          </td>
                          {isAdmin && <td className="py-2.5 pr-4">
                            {blend.cost_per_ton
                              ? `R${blend.cost_per_ton.toFixed(0)}`
                              : "-"}
                          </td>}
                          <td className="py-2.5 pr-4 text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="size-3" />
                              {new Date(
                                blend.created_at
                              ).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="py-2.5">
                            <div className="flex items-center gap-1">
                              <Button
                                size="icon-xs"
                                variant="ghost"
                                onClick={() =>
                                  handleDownloadPdf(
                                    "blend",
                                    blend.id,
                                    blend.blend_name || "blend"
                                  )
                                }
                                title="Download PDF"
                              >
                                <Download className="size-3.5" />
                              </Button>
                              <Button
                                size="icon-xs"
                                variant="ghost"
                                onClick={() =>
                                  setDeleteTarget({
                                    type: "blend",
                                    id: blend.id,
                                    name:
                                      blend.blend_name || "this blend",
                                  })
                                }
                                title="Delete"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="size-3.5" />
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
        )}

        {/* ── Deleted Tab (admin only) ────────────────────────── */}
        {activeTab === "deleted" && isAdmin && (
          <Card>
            <CardHeader>
              <CardTitle>
                Deleted Records ({filteredDeleted.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Filter dropdowns */}
              <div className="mb-4 flex flex-wrap gap-3">
                <select
                  value={deletedTypeFilter}
                  onChange={(e) => setDeletedTypeFilter(e.target.value as "all" | "blend" | "soil_analysis")}
                  className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                >
                  <option value="all">All Types</option>
                  <option value="blend">Blends</option>
                  <option value="soil_analysis">Soil Analyses</option>
                </select>
                <select
                  value={deletedUserFilter}
                  onChange={(e) => setDeletedUserFilter(e.target.value)}
                  className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                >
                  <option value="all">All Users</option>
                  {deletedByUsers.map(([id, name]) => (
                    <option key={id} value={id}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>

              {deletedLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
                </div>
              ) : filteredDeleted.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  {search || deletedTypeFilter !== "all" || deletedUserFilter !== "all"
                    ? "No deleted records match your filters"
                    : "No deleted records"}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4 font-medium">Type</th>
                        <th className="pb-2 pr-4 font-medium">Name</th>
                        <th className="pb-2 pr-4 font-medium">Detail</th>
                        <th className="pb-2 pr-4 font-medium">Deleted By</th>
                        <th className="pb-2 pr-4 font-medium">Deleted At</th>
                        <th className="pb-2 font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredDeleted.map((record) => {
                        const isExpanded = expandedDeletedId === `${record._type}-${record.id}`;
                        return (
                          <React.Fragment key={`${record._type}-${record.id}`}>
                            <tr className="border-b last:border-0">
                              <td className="py-2.5 pr-4">
                                <span
                                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                    record._type === "blend"
                                      ? "bg-blue-50 text-blue-700"
                                      : "bg-green-50 text-green-700"
                                  }`}
                                >
                                  {record._type === "blend" ? "Blend" : "Soil Analysis"}
                                </span>
                              </td>
                              <td className="py-2.5 pr-4 font-medium">
                                {record._name || "-"}
                              </td>
                              <td className="py-2.5 pr-4">
                                {record._detail || "-"}
                              </td>
                              <td className="py-2.5 pr-4">
                                {profiles[record.deleted_by] || record.deleted_by.slice(0, 8)}
                              </td>
                              <td className="py-2.5 pr-4 text-muted-foreground">
                                <span className="flex items-center gap-1">
                                  <Calendar className="size-3" />
                                  {new Date(record.deleted_at).toLocaleDateString()}
                                </span>
                              </td>
                              <td className="py-2.5">
                                <div className="flex items-center gap-1">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() =>
                                      setExpandedDeletedId(
                                        isExpanded ? null : `${record._type}-${record.id}`
                                      )
                                    }
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="mr-1 size-3.5" />
                                    ) : (
                                      <Eye className="mr-1 size-3.5" />
                                    )}
                                    {isExpanded ? "Hide" : "View"}
                                  </Button>
                                  {isAdmin && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="text-green-700 border-green-300 hover:bg-green-50"
                                      onClick={async () => {
                                        try {
                                          const endpoint = record._type === "blend"
                                            ? `/api/blends/${record.id}/restore`
                                            : `/api/soil/${record.id}/restore`;
                                          await api.post(endpoint);
                                          fetchDeletedRecords();
                                          fetchBlends();
                                          fetchSoilRecords();
                                        } catch {}
                                      }}
                                    >
                                      <RotateCcw className="mr-1 size-3.5" />
                                      Restore
                                    </Button>
                                  )}
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() =>
                                      setPermDeleteTarget({
                                        type: record._type,
                                        id: record.id,
                                        name: record._name || "this record",
                                      })
                                    }
                                  >
                                    <Trash2 className="mr-1 size-3.5" />
                                    Delete
                                  </Button>
                                </div>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr>
                                <td colSpan={6} className="p-0">
                                  <div className="rounded-b-md bg-gray-50 px-6 py-4">
                                    {record._type === "blend" ? (
                                      <ExpandedBlendView record={record} isAdmin={isAdmin} />
                                    ) : (
                                      <ExpandedSoilView record={record} />
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* ── Soil Tab ──────────────────────────────────────────── */}
        {activeTab === "soil" && (
          <Card>
            <CardHeader>
              <CardTitle>
                {soilLabel} ({filteredSoil.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {soilLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
                </div>
              ) : filteredSoil.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  {search
                    ? "No analyses match your search"
                    : "No saved soil analyses yet"}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4 font-medium">Crop</th>
                        <th className="pb-2 pr-4 font-medium">Cultivar</th>
                        <th className="pb-2 pr-4 font-medium">Lab</th>
                        {isAdmin && <th className="pb-2 pr-4 font-medium">Cost/ha</th>}
                        <th className="pb-2 pr-4 font-medium">Date</th>
                        <th className="pb-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSoil.map((record) => (
                        <tr
                          key={record.id}
                          onClick={() => preview.openPreview("soil", record.id)}
                          className="cursor-pointer border-b last:border-0 hover:bg-gray-50"
                        >
                          <td className="py-2.5 pr-4 font-medium">
                            {record.crop || "-"}
                          </td>
                          <td className="py-2.5 pr-4">
                            {record.cultivar || "-"}
                          </td>
                          <td className="py-2.5 pr-4">
                            {record.lab_name || "-"}
                          </td>
                          {isAdmin && <td className="py-2.5 pr-4">
                            {record.total_cost_ha
                              ? `R${record.total_cost_ha.toFixed(0)}`
                              : "-"}
                          </td>}
                          <td className="py-2.5 pr-4 text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Calendar className="size-3" />
                              {new Date(
                                record.created_at
                              ).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="py-2.5">
                            <div className="flex items-center gap-1">
                              <Button
                                size="icon-xs"
                                variant="ghost"
                                onClick={() =>
                                  handleDownloadPdf(
                                    "soil",
                                    record.id,
                                    record.crop || "soil-analysis"
                                  )
                                }
                                title="Download PDF"
                              >
                                <Download className="size-3.5" />
                              </Button>
                              <Button
                                size="icon-xs"
                                variant="ghost"
                                onClick={() =>
                                  setDeleteTarget({
                                    type: "soil",
                                    id: record.id,
                                    name:
                                      record.crop ||
                                      "this soil analysis",
                                  })
                                }
                                title="Delete"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="size-3.5" />
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
        )}
      </div>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Record"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        loading={deleting}
      />

      {/* Permanent delete confirmation (admin) */}
      <ConfirmDialog
        open={permDeleteTarget !== null}
        onClose={() => setPermDeleteTarget(null)}
        onConfirm={handlePermanentDelete}
        title="Permanently Delete Record"
        message={`This action cannot be undone. Are you sure you want to permanently delete "${permDeleteTarget?.name}"?`}
        loading={permDeleting}
      />
      <RecordPreviewSheet
        record={preview.record}
        data={preview.data}
        loading={preview.loading}
        onClose={preview.closePreview}
      />
    </AppShell>
  );
}
