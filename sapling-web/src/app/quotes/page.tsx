"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { QuoteThread } from "@/components/quote-thread";
import { QuoteRequestDialog } from "@/components/quote-request-dialog";
import { ClientSelector } from "@/components/client-selector";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  FileText,
  Loader2,
  ChevronDown,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Plus,
  Download,
  Search,
} from "lucide-react";
import { toast } from "sonner";

interface Quote {
  id: string;
  quote_number: string;
  agent_id: string;
  quote_type: string;
  client_name: string;
  farm_name: string | null;
  status: string;
  quoted_price: number | null;
  price_unit: string | null;
  valid_until: string | null;
  request_data: Record<string, unknown>;
  agent_notes: string | null;
  unread_count: number;
  created_at: string;
  messages?: Array<Record<string, unknown>>;
}

const STATUS_BADGES: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: "Pending", color: "bg-yellow-100 text-yellow-700", icon: Clock },
  quoted: { label: "Quoted", color: "bg-purple-100 text-purple-700", icon: FileText },
  accepted: { label: "Accepted", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  declined: { label: "Declined", color: "bg-red-100 text-red-700", icon: XCircle },
  revision_requested: { label: "Revision", color: "bg-orange-100 text-orange-700", icon: AlertTriangle },
  cancelled: { label: "Cancelled", color: "bg-gray-100 text-gray-500", icon: XCircle },
};

const TYPE_LABELS: Record<string, string> = {
  blend: "Blend",
  feeding_program: "Program",
  nutrient_request: "Nutrient",
  blend_assist: "Blend Assist",
};

export default function QuotesPage() {
  const { profile } = useAuth();
  const isAdmin = useEffectiveAdmin();
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);

  // Plain nutrient request form
  const [showNutrientForm, setShowNutrientForm] = useState(false);
  const [nutrientClient, setNutrientClient] = useState("");
  const [nutrientFarm, setNutrientFarm] = useState("");
  const [nutrientData, setNutrientData] = useState({ N: "", P: "", K: "", Ca: "", Mg: "", S: "", batch_size: "1000" });
  const [nutrientMode, setNutrientMode] = useState<"international" | "sa">("international");
  const [saRatio, setSaRatio] = useState({ N: "", P: "", K: "" });
  const [saTotalPct, setSaTotalPct] = useState("");
  const [nutrientNotes, setNutrientNotes] = useState("");
  const [nutrientSubmitting, setNutrientSubmitting] = useState(false);

  const fetchQuotes = useCallback(async () => {
    setLoading(true);
    try {
      let url = "/api/quotes";
      if (filterStatus) url += `?status=${filterStatus}`;
      const data = await api.getAll<Quote>(url);
      // Sort: accepted > pending > quoted > revision_requested > declined > cancelled
      const statusOrder: Record<string, number> = {
        accepted: 0, pending: 1, quoted: 2, revision_requested: 3, declined: 4, cancelled: 5,
      };
      data.sort((a, b) => {
        const sa = statusOrder[a.status] ?? 99;
        const sb = statusOrder[b.status] ?? 99;
        if (sa !== sb) return sa - sb;
        // Within same status, newest first
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setQuotes(data);
    } catch {
      toast.error("Failed to load quotes");
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    fetchQuotes();
  }, [fetchQuotes]);

  async function openQuote(q: Quote) {
    setSheetLoading(true);
    setSelectedQuote(q);
    try {
      const full = await api.get<Quote>(`/api/quotes/${q.id}`);
      setSelectedQuote(full);
    } catch {
    } finally {
      setSheetLoading(false);
    }
  }

  async function handleAction(action: "accept" | "decline" | "revision" | "cancel", content?: string) {
    if (!selectedQuote) return;
    try {
      await api.post(`/api/quotes/${selectedQuote.id}/${action}`, { content });
      toast.success(
        action === "accept" ? "Quote accepted!" :
        action === "decline" ? "Quote declined" :
        action === "cancel" ? "Quote cancelled" :
        "Revision requested"
      );
      setSelectedQuote(null);
      fetchQuotes();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action failed");
    }
  }

  async function submitNutrientRequest() {
    if (!nutrientClient) {
      toast.error("Please select a client");
      return;
    }
    setNutrientSubmitting(true);
    try {
      const requestData: Record<string, unknown> = { batch_size: parseInt(nutrientData.batch_size) || 1000 };
      if (nutrientMode === "international") {
        requestData.targets = {};
        for (const [k, v] of Object.entries(nutrientData)) {
          if (k !== "batch_size" && v) (requestData.targets as Record<string, number>)[k] = parseFloat(v);
        }
        const n = parseFloat(nutrientData.N) || 0;
        const p = parseFloat(nutrientData.P) || 0;
        const k = parseFloat(nutrientData.K) || 0;
        requestData.international_notation = `N ${n}% P ${p}% K ${k}%`;
      } else {
        requestData.sa_ratio = saRatio;
        requestData.sa_total_pct = saTotalPct;
        requestData.sa_notation = `${saRatio.N}:${saRatio.P}:${saRatio.K} (${saTotalPct})`;
      }

      await api.post("/api/quotes", {
        quote_type: "nutrient_request",
        client_name: nutrientClient,
        farm_name: nutrientFarm || null,
        request_data: requestData,
        agent_notes: nutrientNotes || null,
      });
      toast.success("Nutrient quote request submitted!");
      setShowNutrientForm(false);
      setNutrientData({ N: "", P: "", K: "", Ca: "", Mg: "", S: "", batch_size: "1000" });
      setNutrientNotes("");
      fetchQuotes();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to submit");
    } finally {
      setNutrientSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Quotes</h1>
            <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
              Track your quote requests and responses
            </p>
          </div>
          <div className="flex items-center gap-3">
            {!isAdmin && (
              <Button
                variant="outline"
                onClick={() => setShowNutrientForm(!showNutrientForm)}
              >
                <Plus className="size-3.5" />
                Nutrient Request
              </Button>
            )}
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ref, client..."
                className="h-8 rounded-md border border-input bg-white pl-8 pr-3 text-sm w-44 focus:w-56 transition-all focus:outline-none focus:ring-1 focus:ring-[var(--sapling-orange)]"
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
                <option value="revision_requested">Revision</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>
        </div>

        {/* Nutrient Request Form */}
        {showNutrientForm && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Request Nutrient Quote</CardTitle>
              <CardDescription>Enter your nutrient requirements without running the calculator</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Client *</Label>
                    <Input
                      value={nutrientClient}
                      onChange={(e) => setNutrientClient(e.target.value)}
                      placeholder="Client name"
                    />
                  </div>
                  <div>
                    <Label>Farm</Label>
                    <Input
                      value={nutrientFarm}
                      onChange={(e) => setNutrientFarm(e.target.value)}
                      placeholder="Farm name"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button size="sm" variant={nutrientMode === "international" ? "default" : "outline"} onClick={() => setNutrientMode("international")}>
                    International (%)
                  </Button>
                  <Button size="sm" variant={nutrientMode === "sa" ? "default" : "outline"} onClick={() => setNutrientMode("sa")}>
                    SA Notation
                  </Button>
                </div>

                {nutrientMode === "international" ? (
                  <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
                    {["N", "P", "K", "Ca", "Mg", "S"].map((nut) => (
                      <div key={nut}>
                        <Label className="text-xs">{nut} %</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={(nutrientData as Record<string, string>)[nut] || ""}
                          onChange={(e) => setNutrientData((d) => ({ ...d, [nut]: e.target.value }))}
                          className="h-8 text-xs"
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-4 gap-3">
                    {["N", "P", "K"].map((nut) => (
                      <div key={nut}>
                        <Label className="text-xs">{nut} Ratio</Label>
                        <Input
                          type="number"
                          value={(saRatio as Record<string, string>)[nut] || ""}
                          onChange={(e) => setSaRatio((r) => ({ ...r, [nut]: e.target.value }))}
                          className="h-8 text-xs"
                        />
                      </div>
                    ))}
                    <div>
                      <Label className="text-xs">Total %</Label>
                      <Input
                        type="number"
                        value={saTotalPct}
                        onChange={(e) => setSaTotalPct(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">Batch Size (kg)</Label>
                    <Input
                      type="number"
                      value={nutrientData.batch_size}
                      onChange={(e) => setNutrientData((d) => ({ ...d, batch_size: e.target.value }))}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Notes</Label>
                    <Input
                      value={nutrientNotes}
                      onChange={(e) => setNutrientNotes(e.target.value)}
                      placeholder="Additional info..."
                      className="h-8 text-xs"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => setShowNutrientForm(false)}>Cancel</Button>
                  <Button size="sm" onClick={submitNutrientRequest} disabled={nutrientSubmitting || !nutrientClient}>
                    {nutrientSubmitting ? "Submitting..." : "Submit Request"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quote list — skeleton rows while the request is in flight
            so the page doesn't reflow when results arrive. */}
        {loading ? (
          <div
            className="rounded-lg border bg-white"
            aria-busy="true"
            aria-label="Loading quotes"
          >
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex animate-pulse items-center gap-4 border-b px-4 py-3 last:border-0"
              >
                <div className="h-3 w-20 rounded bg-muted" />
                <div className="h-3 w-24 rounded bg-muted/70" />
                <div className="h-3 w-32 rounded bg-muted/70" />
                <div className="ml-auto h-5 w-16 rounded-full bg-muted/70" />
              </div>
            ))}
          </div>
        ) : quotes.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">No quote requests yet</p>
            </CardContent>
          </Card>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Quote #</th>
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
                }).map((q) => {
                  const badge = STATUS_BADGES[q.status] || STATUS_BADGES.pending;
                  return (
                    <tr
                      key={q.id}
                      role="button"
                      tabIndex={0}
                      aria-label={`Open quote ${q.quote_number}`}
                      onClick={() => openQuote(q)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          openQuote(q);
                        }
                      }}
                      className="cursor-pointer hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--sapling-orange)] focus-visible:ring-inset"
                    >
                      <td className="px-4 py-3 font-mono text-xs font-medium text-[var(--sapling-dark)]">
                        {q.quote_number}
                        {q.unread_count > 0 && (
                          <span className="ml-2 inline-flex size-5 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-[10px] font-bold text-white">
                            {q.unread_count}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {TYPE_LABELS[q.quote_type] || q.quote_type}
                      </td>
                      <td className="px-4 py-3">{q.client_name}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${badge.color}`}>
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 tabular-nums">
                        {q.quoted_price != null
                          ? `R${q.quoted_price.toLocaleString("en-ZA", { minimumFractionDigits: 2 })} ${q.price_unit || ""}`
                          : "-"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {new Date(q.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quote Detail Sheet */}
      <Sheet
        open={!!selectedQuote}
        onOpenChange={(open) => { if (!open) { setSelectedQuote(null); fetchQuotes(); } }}
      >
        <SheetContent side="right" className="sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              {selectedQuote?.quote_number || "Quote Details"}
            </SheetTitle>
          </SheetHeader>
          <div className="px-4 pb-4">
            {sheetLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
              </div>
            ) : selectedQuote ? (
              <div className="space-y-4">
                {/* Status + summary */}
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${
                    STATUS_BADGES[selectedQuote.status]?.color || ""
                  }`}>
                    {STATUS_BADGES[selectedQuote.status]?.label || selectedQuote.status}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {TYPE_LABELS[selectedQuote.quote_type] || selectedQuote.quote_type} for {selectedQuote.client_name}
                  </span>
                </div>

                {/* Price display for quoted items */}
                {selectedQuote.quoted_price != null && (
                  <div className="rounded-lg bg-purple-50 p-4 text-center">
                    <p className="text-xs text-purple-600">Quoted Price</p>
                    <p className="text-2xl font-bold text-purple-800">
                      R{selectedQuote.quoted_price.toLocaleString("en-ZA", { minimumFractionDigits: 2 })}
                    </p>
                    <p className="text-xs text-purple-600">{selectedQuote.price_unit || ""}</p>
                    {selectedQuote.valid_until && (
                      <p className="mt-1 text-xs text-purple-500">Valid until {selectedQuote.valid_until}</p>
                    )}
                  </div>
                )}

                {/* Download quote PDF — when quoted or accepted */}
                {selectedQuote.quoted_price != null && (selectedQuote.status === "quoted" || selectedQuote.status === "accepted") && (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const blob = await api.getPdf(`/api/quotes/${selectedQuote.id}/pdf`);
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `Quote_${selectedQuote.quote_number}.pdf`;
                        a.click();
                        URL.revokeObjectURL(url);
                      } catch {
                        toast.error("Download failed");
                      }
                    }}
                  >
                    <Download className="size-4" />
                    Download Quote PDF
                  </Button>
                )}

                {/* Action buttons for quoted status */}
                {selectedQuote.status === "quoted" && (
                  <div className="flex gap-2">
                    <Button
                      className="flex-1 bg-green-600 text-white hover:bg-green-700"
                      onClick={() => handleAction("accept")}
                    >
                      <CheckCircle2 className="size-4" />
                      Accept
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        const reason = prompt("Reason for declining (optional):");
                        handleAction("decline", reason || undefined);
                      }}
                    >
                      <XCircle className="size-4" />
                      Decline
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        const notes = prompt("What changes would you like?");
                        if (notes) handleAction("revision", notes);
                      }}
                    >
                      <AlertTriangle className="size-4" />
                      Revise
                    </Button>
                  </div>
                )}

                {/* Cancel button — available on pending/quoted/revision statuses */}
                {selectedQuote.status && !["accepted", "declined", "cancelled"].includes(selectedQuote.status) && (
                  <Button
                    variant="outline"
                    className="w-full text-red-600 hover:bg-red-50 hover:text-red-700"
                    onClick={() => {
                      const reason = prompt("Reason for cancellation (optional):");
                      if (reason !== null) {
                        handleAction("cancel", reason || undefined);
                      }
                    }}
                  >
                    <XCircle className="size-4" />
                    Cancel Quote Request
                  </Button>
                )}

                {/* Communication thread */}
                <div className="border-t pt-4">
                  <h3 className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Communication</h3>
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
    </AppShell>
  );
}
