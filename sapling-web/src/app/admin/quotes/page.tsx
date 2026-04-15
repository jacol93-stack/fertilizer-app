"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { QuoteThread } from "@/components/quote-thread";
import {
  Loader2,
  ChevronDown,
  Clock,
  CheckCircle2,
  FileText,
  Send,
  Eye,
  FlaskConical,
  Search,
} from "lucide-react";
import { useRecordPreview, RecordPreviewSheet } from "@/components/record-preview-sheet";
import { toast } from "sonner";

interface Quote {
  id: string;
  quote_number: string;
  agent_id: string;
  agent_name?: string;
  agent_email?: string;
  quote_type: string;
  client_name: string;
  farm_name: string | null;
  field_name: string | null;
  status: string;
  quoted_price: number | null;
  price_unit: string | null;
  valid_until: string | null;
  request_data: Record<string, unknown>;
  agent_notes: string | null;
  blend_id: string | null;
  soil_analysis_id: string | null;
  feeding_plan_id: string | null;
  unread_count: number;
  payment_terms: string | null;
  delivery_date_from: string | null;
  delivery_date_to: string | null;
  delivery_notes: string | null;
  created_at: string;
  messages?: Array<Record<string, unknown>>;
}

const PAYMENT_LABELS: Record<string, string> = {
  payment_at_order: "Payment at order",
  payment_on_delivery: "Payment on delivery",
  "30_days": "30 days",
  other: "Other",
};

interface Stats {
  pending: number;
  quoted: number;
  accepted: number;
  revision_requested: number;
  total: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  quoted: "bg-purple-100 text-purple-700",
  accepted: "bg-green-100 text-green-700",
  declined: "bg-red-100 text-red-700",
  revision_requested: "bg-orange-100 text-orange-700",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  quoted: "Quoted",
  accepted: "Accepted",
  declined: "Declined",
  revision_requested: "Revision",
};

const TYPE_LABELS: Record<string, string> = {
  blend: "Blend",
  feeding_program: "Program",
  nutrient_request: "Nutrient",
};

export default function AdminQuotesPageWrapper() {
  return (
    <Suspense>
      <AdminQuotesPage />
    </Suspense>
  );
}

function AdminQuotesPage() {
  const { isAdmin, isLoading: authLoading, profile } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);
  const blendPreview = useRecordPreview();

  // Pricing form
  const [priceInput, setPriceInput] = useState("");
  const [priceUnit, setPriceUnit] = useState("per_ton");
  const [validUntil, setValidUntil] = useState("");
  const [adminNotes, setAdminNotes] = useState("");
  const [sendingQuote, setSendingQuote] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAdmin) router.replace("/");
  }, [authLoading, isAdmin]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let url = "/api/quotes/admin/list";
      if (filterStatus) url += `?status=${filterStatus}`;
      const [quotesData, statsData] = await Promise.all([
        api.get<Quote[]>(url),
        api.get<Stats>("/api/quotes/admin/stats"),
      ]);
      // Sort: accepted > pending > quoted > revision_requested > declined > cancelled
      const statusOrder: Record<string, number> = {
        accepted: 0, pending: 1, quoted: 2, revision_requested: 3, declined: 4, cancelled: 5,
      };
      quotesData.sort((a, b) => {
        const sa = statusOrder[a.status] ?? 99;
        const sb2 = statusOrder[b.status] ?? 99;
        if (sa !== sb2) return sa - sb2;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setQuotes(quotesData);
      setStats(statsData);
    } catch {
      toast.error("Failed to load quotes");
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    if (!authLoading && isAdmin) fetchData();
  }, [authLoading, isAdmin, fetchData]);

  // Auto-open quote from URL param (once only)
  const [autoOpened, setAutoOpened] = useState(false);
  useEffect(() => {
    const id = searchParams.get("id");
    if (id && quotes.length > 0 && !autoOpened && !selectedQuote) {
      const q = quotes.find((q) => q.id === id);
      if (q) {
        openQuote(q);
        setAutoOpened(true);
      }
    }
  }, [searchParams, quotes]);

  async function openQuote(q: Quote) {
    setSheetLoading(true);
    setSelectedQuote(q);
    setPriceInput(q.quoted_price?.toString() || "");
    setPriceUnit(q.price_unit || "per_ton");
    setValidUntil(q.valid_until || "");
    setAdminNotes("");
    try {
      const full = await api.get<Quote>(`/api/quotes/${q.id}`);
      setSelectedQuote(full);
    } catch {
    } finally {
      setSheetLoading(false);
    }
  }

  async function handleSendQuote() {
    if (!selectedQuote || !priceInput) return;
    setSendingQuote(true);
    try {
      await api.post(`/api/quotes/admin/${selectedQuote.id}/quote`, {
        quoted_price: parseFloat(priceInput),
        price_unit: priceUnit,
        valid_until: validUntil || null,
        admin_notes: adminNotes || null,
      });
      toast.success("Quote sent to agent!");
      setSelectedQuote(null);
      fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send quote");
    } finally {
      setSendingQuote(false);
    }
  }

  if (authLoading) return null;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Quote Management</h1>
          <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
            Review and respond to agent quote requests
          </p>
        </div>

        {/* Stats cards */}
        {stats && (
          <div className="mb-6 grid gap-4 sm:grid-cols-4">
            <Card size="sm">
              <CardContent>
                <div className="flex items-center gap-3">
                  <Clock className="size-5 text-yellow-500" />
                  <div>
                    <p className="text-2xl font-bold">{stats.pending}</p>
                    <p className="text-xs text-muted-foreground">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card size="sm">
              <CardContent>
                <div className="flex items-center gap-3">
                  <FileText className="size-5 text-purple-500" />
                  <div>
                    <p className="text-2xl font-bold">{stats.quoted}</p>
                    <p className="text-xs text-muted-foreground">Quoted</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card size="sm">
              <CardContent>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="size-5 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">{stats.accepted}</p>
                    <p className="text-xs text-muted-foreground">Accepted</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card size="sm">
              <CardContent>
                <div className="flex items-center gap-3">
                  <FileText className="size-5 text-[var(--sapling-orange)]" />
                  <div>
                    <p className="text-2xl font-bold">{stats.total}</p>
                    <p className="text-xs text-muted-foreground">Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Search & Filter */}
        <div className="mb-4 flex items-center justify-end gap-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ref, client, product..."
              className="h-8 rounded-md border border-input bg-white pl-8 pr-3 text-sm w-48 focus:w-64 transition-all focus:outline-none focus:ring-1 focus:ring-[var(--sapling-orange)]"
            />
          </div>
          <div className="relative">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-8 appearance-none rounded-md border border-input bg-white pl-3 pr-8 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="quoted">Quoted</option>
              <option value="accepted">Accepted</option>
              <option value="declined">Declined</option>
              <option value="revision_requested">Revision Requested</option>
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>

        {/* Quote table */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Quote #</th>
                  <th className="px-4 py-3">Agent</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Client</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {quotes.filter((q) => {
                  if (!searchQuery) return true;
                  const s = searchQuery.toLowerCase();
                  return (
                    q.quote_number.toLowerCase().includes(s) ||
                    q.client_name.toLowerCase().includes(s) ||
                    (q.farm_name || "").toLowerCase().includes(s) ||
                    String(q.request_data?.sa_notation || "").toLowerCase().includes(s) ||
                    String(q.request_data?.product_name || "").toLowerCase().includes(s)
                  );
                }).map((q) => (
                  <tr
                    key={q.id}
                    onClick={() => openQuote(q)}
                    className="cursor-pointer hover:bg-gray-50"
                  >
                    <td className="px-4 py-3 font-mono text-xs font-medium text-[var(--sapling-dark)]">
                      {q.quote_number}
                      {q.unread_count > 0 && (
                        <span className="ml-2 inline-flex size-5 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-[10px] font-bold text-white">
                          {q.unread_count}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">{q.agent_name || "-"}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {TYPE_LABELS[q.quote_type] || q.quote_type}
                    </td>
                    <td className="px-4 py-3">{q.client_name}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[q.status] || ""}`}>
                        {STATUS_LABELS[q.status] || q.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular-nums">
                      {q.quoted_price != null ? `R${q.quoted_price.toLocaleString("en-ZA", { minimumFractionDigits: 2 })}` : "-"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(q.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
                {quotes.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                      No quotes found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quote Detail Sheet */}
      <Sheet
        open={!!selectedQuote}
        onOpenChange={(open) => { if (!open) { setSelectedQuote(null); } }}
      >
        <SheetContent side="right" className="sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{selectedQuote?.quote_number || "Quote"}</SheetTitle>
          </SheetHeader>
          <div className="px-4 pb-4">
            {sheetLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
              </div>
            ) : selectedQuote ? (
              <div className="space-y-4">
                {/* Quote info */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded bg-muted px-3 py-2">
                    <p className="text-xs text-muted-foreground">Agent</p>
                    <p className="font-medium">{selectedQuote.agent_name || "-"}</p>
                  </div>
                  <div className="rounded bg-muted px-3 py-2">
                    <p className="text-xs text-muted-foreground">Client</p>
                    <p className="font-medium">{selectedQuote.client_name}</p>
                  </div>
                  <div className="rounded bg-muted px-3 py-2">
                    <p className="text-xs text-muted-foreground">Type</p>
                    <p className="font-medium">{TYPE_LABELS[selectedQuote.quote_type] || selectedQuote.quote_type}</p>
                  </div>
                  <div className="rounded bg-muted px-3 py-2">
                    <p className="text-xs text-muted-foreground">Status</p>
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[selectedQuote.status] || ""}`}>
                      {STATUS_LABELS[selectedQuote.status] || selectedQuote.status}
                    </span>
                  </div>
                </div>

                {/* Request data */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">Request Details</CardTitle>
                      {selectedQuote.blend_id && (
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            blendPreview.openPreview("blend", selectedQuote.blend_id!);
                          }}
                        >
                          <Eye className="size-3" />
                          View Blend
                        </Button>
                      )}
                      {selectedQuote.soil_analysis_id && (
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            blendPreview.openPreview("soil", selectedQuote.soil_analysis_id!);
                          }}
                        >
                          <Eye className="size-3" />
                          View Analysis
                        </Button>
                      )}
                      {selectedQuote.quote_type === "blend" && (
                        <Button
                          size="xs"
                          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                          onClick={() => {
                            // Save quote data to session so blend page can pick it up
                            sessionStorage.setItem("quote_prefill", JSON.stringify({
                              quote_id: selectedQuote.id,
                              quote_number: selectedQuote.quote_number,
                              client_name: selectedQuote.client_name,
                              farm_name: selectedQuote.farm_name,
                              ...selectedQuote.request_data,
                            }));
                            window.location.href = "/quick-blend";
                          }}
                        >
                          <FlaskConical className="size-3" />
                          Open in Blend Calculator
                        </Button>
                      )}
                      {selectedQuote.quote_type === "nutrient_request" && (
                        <Button
                          size="xs"
                          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                          onClick={() => {
                            sessionStorage.setItem("quote_prefill", JSON.stringify({
                              quote_id: selectedQuote.id,
                              quote_number: selectedQuote.quote_number,
                              client_name: selectedQuote.client_name,
                              farm_name: selectedQuote.farm_name,
                              ...selectedQuote.request_data,
                            }));
                            window.location.href = "/quick-blend";
                          }}
                        >
                          <FlaskConical className="size-3" />
                          Open in Blend Calculator
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const rd = selectedQuote.request_data || {};
                      const targets = rd.targets as Record<string, number> | undefined;
                      const nutrients = rd.nutrients as Array<Record<string, unknown>> | undefined;
                      return (
                        <div className="space-y-3">
                          {/* Key fields */}
                          <div className="space-y-1 text-sm">
                            {rd.sa_notation ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">SA Notation</span>
                                <span className="font-bold text-lg">{String(rd.sa_notation)}</span>
                              </div>
                            ) : null}
                            {rd.international_notation ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">International</span>
                                <span className="font-medium">{String(rd.international_notation)}</span>
                              </div>
                            ) : null}
                            {rd.batch_size ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Batch Size</span>
                                <span className="font-medium">{Number(rd.batch_size).toLocaleString()} kg</span>
                              </div>
                            ) : null}
                            {rd.min_compost_pct != null ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Min Compost</span>
                                <span className="font-medium">{String(rd.min_compost_pct)}%</span>
                              </div>
                            ) : null}
                            {rd.blend_mode ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Blend Mode</span>
                                <span className="font-medium">{String(rd.blend_mode)}</span>
                              </div>
                            ) : null}
                            {Array.isArray(rd.preferences) && rd.preferences.length > 0 ? (
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Preferences</span>
                                <span className="font-medium">{(rd.preferences as string[]).join(", ")}</span>
                              </div>
                            ) : null}
                          </div>

                          {/* Targets table (from nutrient_request) */}
                          {targets && typeof targets === "object" && !Array.isArray(targets) && (
                            <div className="overflow-x-auto rounded-lg border border-gray-200">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b bg-gray-50 text-left font-medium text-gray-500">
                                    <th className="px-3 py-1.5">Nutrient</th>
                                    <th className="px-3 py-1.5 text-right">Target %</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                  {Object.entries(targets).filter(([, v]) => v > 0).map(([nut, val]) => (
                                    <tr key={nut}>
                                      <td className="px-3 py-1.5 font-medium">{nut}</td>
                                      <td className="px-3 py-1.5 text-right tabular-nums">{Number(val).toFixed(2)}%</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}

                          {/* Nutrients table (from blend optimizer results) */}
                          {Array.isArray(nutrients) && nutrients.length > 0 && (
                            <div className="overflow-x-auto rounded-lg border border-gray-200">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b bg-gray-50 text-left font-medium text-gray-500">
                                    <th className="px-3 py-1.5">Nutrient</th>
                                    <th className="px-3 py-1.5 text-right">Target %</th>
                                    <th className="px-3 py-1.5 text-right">Actual %</th>
                                    <th className="px-3 py-1.5 text-right">kg/ton</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                  {nutrients
                                    .filter((n) => Number(n.target) > 0 || Number(n.actual) > 0.1)
                                    .map((n) => (
                                      <tr key={String(n.nutrient)}>
                                        <td className="px-3 py-1.5 font-medium">{String(n.nutrient)}</td>
                                        <td className="px-3 py-1.5 text-right tabular-nums">{Number(n.target).toFixed(2)}</td>
                                        <td className="px-3 py-1.5 text-right tabular-nums">{Number(n.actual).toFixed(2)}</td>
                                        <td className="px-3 py-1.5 text-right tabular-nums">{Number(n.kg_per_ton).toFixed(1)}</td>
                                      </tr>
                                    ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                    {/* Payment & delivery info */}
                    <div className="mt-3 space-y-1 border-t pt-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Payment Terms</span>
                        <span className="font-medium">{PAYMENT_LABELS[selectedQuote.payment_terms || ""] || selectedQuote.payment_terms || "-"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Delivery Window</span>
                        <span className="font-medium">
                          {selectedQuote.delivery_date_from
                            ? `${selectedQuote.delivery_date_from}${selectedQuote.delivery_date_to ? ` to ${selectedQuote.delivery_date_to}` : ""}`
                            : "-"}
                        </span>
                      </div>
                      {selectedQuote.delivery_notes && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Delivery Notes</span>
                          <span className="font-medium">{selectedQuote.delivery_notes}</span>
                        </div>
                      )}
                      {selectedQuote.agent_notes && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Agent Notes</span>
                          <span className="font-medium">{selectedQuote.agent_notes}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Pricing form — for pending or revision_requested */}
                {(selectedQuote.status === "pending" || selectedQuote.status === "revision_requested") && (
                  <Card className="border-2 border-purple-200">
                    <CardHeader>
                      <CardTitle className="text-sm text-purple-700">Set Price & Send Quote</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label className="text-xs">Price (R)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={priceInput}
                              onChange={(e) => setPriceInput(e.target.value)}
                              placeholder="0.00"
                              className="h-8"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Unit</Label>
                            <select
                              value={priceUnit}
                              onChange={(e) => setPriceUnit(e.target.value)}
                              className="h-8 w-full rounded-md border border-input bg-white px-2.5 text-sm"
                            >
                              <option value="per_ton">per ton</option>
                              <option value="per_ha">per hectare</option>
                              <option value="total">total</option>
                              <option value="per_bag">per bag</option>
                            </select>
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs">Valid Until</Label>
                          <Input
                            type="date"
                            value={validUntil}
                            onChange={(e) => setValidUntil(e.target.value)}
                            className="h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">Notes to Agent</Label>
                          <textarea
                            value={adminNotes}
                            onChange={(e) => setAdminNotes(e.target.value)}
                            placeholder="Any notes about this quote..."
                            className="h-16 w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring"
                          />
                        </div>
                        <Button
                          onClick={handleSendQuote}
                          disabled={sendingQuote || !priceInput}
                          className="w-full bg-purple-600 text-white hover:bg-purple-700"
                        >
                          {sendingQuote ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                          {sendingQuote ? "Sending..." : "Send Quote to Agent"}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Communication thread */}
                <div className="border-t pt-4">
                  <h3 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Communication Thread</h3>
                  <QuoteThread
                    messages={(selectedQuote.messages || []) as any}
                    quoteId={selectedQuote.id}
                    currentUserId={profile?.id || ""}
                    onMessageSent={() => openQuote(selectedQuote)}
                  />
                </div>
              </div>
            ) : null}
          </div>
        </SheetContent>
      </Sheet>

      <RecordPreviewSheet
        record={blendPreview.record}
        data={blendPreview.data}
        loading={blendPreview.loading}
        onClose={blendPreview.closePreview}
      />
    </AppShell>
  );
}
