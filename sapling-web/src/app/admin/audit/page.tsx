"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ChevronDown, Eye, Download } from "lucide-react";
import { useRecordPreview, RecordPreviewSheet } from "@/components/record-preview-sheet";

interface AuditEntry {
  id?: string;
  created_at: string;
  user_id: string | null;
  user_role: string | null;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  metadata: Record<string, unknown> | null;
  // Aliases for backward compat
  action?: string;
  table_name?: string;
  record_id?: string;
}

interface UserProfile {
  id: string;
  name: string;
  email: string;
}

const EVENT_TYPES: Array<{ value: string; label: string }> = [
  { value: "", label: "All Events" },
  { value: "blend_draft", label: "Blend Created (unsaved)" },
  { value: "blend_save", label: "Blend Saved" },
  { value: "blend_update", label: "Blend Updated" },
  { value: "blend_soft_delete", label: "Blend Deleted" },
  { value: "blend_pdf_download", label: "Blend PDF Download" },
  { value: "blend_restore", label: "Blend Restored" },
  { value: "soil_draft", label: "Soil Analysis Created (unsaved)" },
  { value: "feeding_plan_draft", label: "Feeding Plan Created (unsaved)" },
  { value: "create", label: "Record Created" },
  { value: "update", label: "Record Updated" },
  { value: "delete", label: "Record Deleted" },
  { value: "soil_analysis_pdf_download", label: "Soil PDF Download" },
  { value: "soil_program_pdf_download", label: "Program PDF Download" },
  { value: "competitor_product", label: "Competitor Product" },
  { value: "application_record", label: "Application Recorded" },
  { value: "programme_generate", label: "Programme Generated" },
  { value: "programme_adjust", label: "Programme Adjusted" },
];

const EVENT_COLORS: Record<string, string> = {
  // Match by substring for flexibility
  blend_save: "bg-green-100 text-green-700",
  blend_update: "bg-orange-100 text-orange-700",
  blend_soft_delete: "bg-red-100 text-red-700",
  blend_hard_delete: "bg-red-100 text-red-700",
  blend_restore: "bg-blue-100 text-blue-700",
  blend_pdf_download: "bg-blue-100 text-blue-700",
  soil_analysis_pdf_download: "bg-blue-100 text-blue-700",
  soil_program_pdf_download: "bg-blue-100 text-blue-700",
  blend_draft: "bg-yellow-100 text-yellow-700",
  soil_draft: "bg-yellow-100 text-yellow-700",
  feeding_plan_draft: "bg-yellow-100 text-yellow-700",
  create: "bg-green-100 text-green-700",
  update: "bg-orange-100 text-orange-700",
  delete: "bg-red-100 text-red-700",
  soft_delete: "bg-red-100 text-red-700",
  hard_delete: "bg-red-100 text-red-700",
  competitor_product: "bg-red-100 text-red-700",
  application_record: "bg-green-100 text-green-700",
  programme_generate: "bg-purple-100 text-purple-700",
  programme_adjust: "bg-amber-100 text-amber-700",
};

const LIMIT = 50;

export default function AuditPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const preview = useRecordPreview();
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  // Filters
  const [filterEvent, setFilterEvent] = useState("");
  const [filterUser, setFilterUser] = useState("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");

  const buildQuery = useCallback(
    (currentOffset: number) => {
      const params = new URLSearchParams();
      params.set("limit", String(LIMIT));
      // Backend param is `skip` not `offset` — kept variable name as
      // currentOffset locally for clarity.
      params.set("skip", String(currentOffset));
      if (filterEvent) params.set("event_type", filterEvent);
      if (filterUser) params.set("user_id", filterUser);
      return `/api/admin/audit-log?${params.toString()}`;
    },
    [filterEvent, filterUser]
  );

  const fetchEntries = useCallback(
    async (append = false) => {
      const currentOffset = append ? offset : 0;
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
        setOffset(0);
      }
      try {
        const res = await api.get<{ items: AuditEntry[]; total: number | null }>(
          buildQuery(currentOffset),
        );
        const data = res.items || [];
        if (append) {
          setEntries((prev) => [...prev, ...data]);
        } else {
          setEntries(data);
        }
        setHasMore(data.length === LIMIT);
        if (append) {
          setOffset(currentOffset + data.length);
        } else {
          setOffset(data.length);
        }
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load audit log");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [buildQuery, offset]
  );

  const fetchUsers = useCallback(async () => {
    try {
      const data = await api.getAll<UserProfile>("/api/admin/users");
      setUsers(data);
    } catch {
      // Non-critical, silently fail
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace("/");
      return;
    }
    if (!authLoading && isAdmin) {
      fetchUsers();
    }
  }, [authLoading, isAdmin, router, fetchUsers]);

  useEffect(() => {
    if (!authLoading && isAdmin) {
      fetchEntries(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isAdmin, filterEvent, filterUser]);

  function getUserName(userId: string | null): string {
    if (!userId) return "-";
    const user = users.find((u) => u.id === userId);
    return user?.name ?? userId.slice(0, 8) + "...";
  }

  function formatTimestamp(ts: string): string {
    try {
      return new Date(ts).toLocaleString("en-ZA", {
        dateStyle: "short",
        timeStyle: "short",
      });
    } catch {
      return ts;
    }
  }

  if (authLoading) return null;

  return (
    <>
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Audit Log</h1>
          <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
            Track all system changes and user activity
          </p>
        </div>

        {/* Filters */}
        <div className="mt-6 flex flex-wrap items-end gap-4">
          <div className="grid gap-1.5">
            <Label className="text-xs text-gray-500">Event Type</Label>
            <select
              className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              value={filterEvent}
              onChange={(e) => setFilterEvent(e.target.value)}
            >
              {EVENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-1.5">
            <Label className="text-xs text-gray-500">User</Label>
            <select
              className="h-8 min-w-[160px] rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              value={filterUser}
              onChange={(e) => setFilterUser(e.target.value)}
            >
              <option value="">All Users</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFilterEvent("");
              setFilterUser("");
              setFilterDateFrom("");
              setFilterDateTo("");
            }}
          >
            Clear Filters
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="mt-8 flex justify-center">
            <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-[var(--sapling-orange)]" />
          </div>
        ) : (
          <>
            <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">User</th>
                    <th className="px-4 py-3">Event</th>
                    <th className="px-4 py-3">Entity</th>
                    <th className="px-4 py-3">Record</th>
                    <th className="px-4 py-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {entries.map((entry, idx) => {
                    const rid = entry.entity_id || entry.record_id;
                    const entityType = entry.entity_type || entry.table_name || "";
                    const isBlend = entityType === "blends" || entityType === "blend";
                    const isSoil = entityType === "soil_analyses";
                    const isPreviewable = rid && (isBlend || isSoil);
                    const previewType = isBlend ? "blend" : "soil";
                    return (
                    <tr
                      key={entry.id ?? idx}
                      onClick={() => isPreviewable && preview.openPreview(previewType as "blend" | "soil", rid!)}
                      className={`hover:bg-gray-50 ${isPreviewable ? "cursor-pointer" : ""}`}
                    >
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                        {formatTimestamp(entry.created_at)}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {getUserName(entry.user_id)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            (() => {
                              const evt = entry.event_type || entry.action || "";
                              if (evt.includes("download")) return "bg-blue-100 text-blue-700";
                              if (evt.includes("delete")) return "bg-red-100 text-red-700";
                              if (evt.includes("update") || evt.includes("restore")) return "bg-orange-100 text-orange-700";
                              if (evt.includes("save") || evt.includes("create")) return "bg-green-100 text-green-700";
                              return "bg-gray-100 text-gray-700";
                            })()
                          }`}
                        >
                          {(entry.event_type || entry.action || "-").replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {(entry.entity_type || entry.table_name || "-").replace(/_/g, " ")}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-xs">
                        {(() => {
                          const rid = entry.entity_id || entry.record_id;
                          if (!rid) return <span className="text-gray-500">-</span>;
                          const entityType = entry.entity_type || entry.table_name || "";
                          const isBlendCell = entityType === "blends" || entityType === "blend";
                          const isSoilCell = entityType === "soil_analyses";
                          const isPreviewable = isBlendCell || isSoilCell;
                          const previewType = isBlendCell ? "blend" : "soil";
                          const display = rid.length > 12 ? rid.slice(0, 12) + "..." : rid;
                          if (isPreviewable) {
                            return (
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => preview.openPreview(previewType as "blend" | "soil", rid)}
                                  className="inline-flex items-center gap-1 text-[var(--sapling-orange)] hover:underline"
                                  title="Preview"
                                >
                                  <Eye className="size-3" />
                                  {display}
                                </button>
                                <button
                                  type="button"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    try {
                                      const pdfPath = previewType === "blend"
                                        ? `/api/reports/blend/${rid}/pdf`
                                        : `/api/reports/soil/${rid}/pdf`;
                                      const blob = await api.getPdf(pdfPath);
                                      const url = URL.createObjectURL(blob);
                                      const a = document.createElement("a");
                                      a.href = url;
                                      a.download = `${previewType}_${rid.slice(0, 8)}.pdf`;
                                      a.click();
                                      URL.revokeObjectURL(url);
                                    } catch {
                                      toast.error("PDF download failed");
                                    }
                                  }}
                                  className="text-gray-400 hover:text-[var(--sapling-orange)]"
                                  title="Download PDF"
                                >
                                  <Download className="size-3" />
                                </button>
                              </div>
                            );
                          }
                          return <span className="font-mono text-gray-500">{display}</span>;
                        })()}
                      </td>
                      <td className="max-w-xs px-4 py-3 text-xs text-gray-500">
                        {(entry.metadata as Record<string, unknown>)?.impersonation ? (
                          <span className="mr-2 inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-700">
                            Impersonated
                          </span>
                        ) : null}
                        <span className="truncate">
                          {entry.metadata && Object.keys(entry.metadata).length > 0
                            ? JSON.stringify(entry.metadata).slice(0, 60)
                            : "-"}
                        </span>
                      </td>
                    </tr>
                  );})}
                  {entries.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                        No audit entries found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {hasMore && entries.length > 0 && (
              <div className="mt-4 flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => fetchEntries(true)}
                  disabled={loadingMore}
                >
                  {loadingMore ? "Loading..." : "Load More"}
                  {!loadingMore && <ChevronDown className="size-4" data-icon="inline-end" />}
                </Button>
              </div>
            )}
          </>
        )}
      </div>
      <RecordPreviewSheet
        record={preview.record}
        data={preview.data}
        loading={preview.loading}
        onClose={preview.closePreview}
      />
    </>
  );
}
