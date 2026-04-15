"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { X, Send, Loader2 } from "lucide-react";

interface QuoteRequestDialogProps {
  open: boolean;
  onClose: () => void;
  quoteType: "blend" | "feeding_program" | "nutrient_request" | "blend_assist";
  requestData: Record<string, unknown>;
  clientName: string;
  clientId?: string;
  farmName?: string;
  fieldName?: string;
  blendId?: string;
  soilAnalysisId?: string;
  feedingPlanId?: string;
  summary?: string; // brief text summary of what's being quoted
}

export function QuoteRequestDialog({
  open,
  onClose,
  quoteType,
  requestData,
  clientName,
  clientId,
  farmName,
  fieldName,
  blendId,
  soilAnalysisId,
  feedingPlanId,
  summary,
}: QuoteRequestDialogProps) {
  const [notes, setNotes] = useState("");
  const [paymentTerms, setPaymentTerms] = useState("");
  const [deliveryFrom, setDeliveryFrom] = useState("");
  const [deliveryTo, setDeliveryTo] = useState("");
  const [deliveryNotes, setDeliveryNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  const typeLabels: Record<string, string> = {
    blend: "Blend Quote",
    feeding_program: "Fertilizer Program Quote",
    nutrient_request: "Nutrient Request",
    blend_assist: "Blend Assistance Request",
  };

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const result = await api.post<{ quote_number: string }>("/api/quotes", {
        quote_type: quoteType,
        client_id: clientId || null,
        client_name: clientName,
        farm_name: farmName || null,
        field_name: fieldName || null,
        blend_id: blendId || null,
        soil_analysis_id: soilAnalysisId || null,
        feeding_plan_id: feedingPlanId || null,
        request_data: requestData,
        agent_notes: notes || null,
        payment_terms: paymentTerms || null,
        delivery_date_from: deliveryFrom || null,
        delivery_date_to: deliveryTo || null,
        delivery_notes: deliveryNotes || null,
      });
      toast.success(`Quote request submitted! Reference: ${result.quote_number}`);
      setNotes("");
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to submit quote request");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
            Request Quote
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="size-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Summary */}
          <div className="rounded-lg bg-orange-50 p-3">
            <p className="text-xs font-medium uppercase tracking-wider text-orange-600">
              {typeLabels[quoteType] || "Quote Request"}
            </p>
            <p className="mt-1 text-sm font-medium text-[var(--sapling-dark)]">
              {clientName}
              {farmName ? ` / ${farmName}` : ""}
              {fieldName ? ` / ${fieldName}` : ""}
            </p>
            {summary && (
              <p className="mt-1 text-xs text-orange-700">{summary}</p>
            )}
          </div>

          {/* Request data preview */}
          {requestData.sa_notation ? (
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="rounded bg-muted px-3 py-2">
                <p className="text-xs text-muted-foreground">SA Notation</p>
                <p className="font-medium">{String(requestData.sa_notation)}</p>
              </div>
              {requestData.international_notation ? (
                <div className="rounded bg-muted px-3 py-2">
                  <p className="text-xs text-muted-foreground">International</p>
                  <p className="font-medium">{String(requestData.international_notation)}</p>
                </div>
              ) : null}
              {requestData.batch_size ? (
                <div className="rounded bg-muted px-3 py-2">
                  <p className="text-xs text-muted-foreground">Batch Size</p>
                  <p className="font-medium">{String(requestData.batch_size)} kg</p>
                </div>
              ) : null}
            </div>
          ) : null}

          {/* Payment terms */}
          <div className="space-y-1.5">
            <Label>Payment Terms</Label>
            <select
              value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value)}
              className="h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring"
            >
              <option value="">Select payment terms...</option>
              <option value="payment_at_order">Payment at order</option>
              <option value="payment_on_delivery">Payment on delivery</option>
              <option value="30_days">30 days</option>
              <option value="other">Other (specify in notes)</option>
            </select>
          </div>

          {/* Delivery date */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Delivery from</Label>
              <Input
                type="date"
                value={deliveryFrom}
                onChange={(e) => setDeliveryFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Delivery to</Label>
              <Input
                type="date"
                value={deliveryTo}
                onChange={(e) => setDeliveryTo(e.target.value)}
              />
            </div>
          </div>

          {/* Agent notes */}
          <div className="space-y-1.5">
            <Label htmlFor="q-notes">Notes (optional)</Label>
            <textarea
              id="q-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any additional details for this quote request..."
              className="h-20 w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={submitting}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {submitting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Send className="size-4" />
              )}
              {submitting ? "Submitting..." : "Submit Request"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
