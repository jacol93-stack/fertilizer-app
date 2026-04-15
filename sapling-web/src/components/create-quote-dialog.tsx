"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { getCompanyProfiles } from "@/lib/auth-context";
import type { CompanyProfile, Profile } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { X } from "lucide-react";
import { toast } from "sonner";
import { Loader2, Send, Building2, Download, Check } from "lucide-react";

interface CreateQuoteDialogProps {
  open: boolean;
  onClose: () => void;
  profile: Profile | null;
  clientName: string;
  clientId?: string;
  farmName?: string;
  /** Pre-filled from Quick Blend selling price — editable in dialog */
  sellingPrice: number;
  savedBlendId?: string | null;
  blendData: {
    sa_notation: string;
    international_notation: string;
    batch_size: number;
    min_compost_pct: number;
    blend_mode: string;
    preferences: string[];
    nutrients: unknown[];
    recipe: unknown[];
    cost_per_ton: number;
  };
}

export function CreateQuoteDialog({
  open,
  onClose,
  profile,
  clientName,
  clientId,
  farmName,
  sellingPrice,
  savedBlendId,
  blendData,
}: CreateQuoteDialogProps) {
  const companies = getCompanyProfiles(profile);
  const hasExistingClient = !!clientName;

  const [selectedCompanyIdx, setSelectedCompanyIdx] = useState(0);
  const [productName, setProductName] = useState(blendData.sa_notation || "");
  const [price, setPrice] = useState(sellingPrice > 0 ? sellingPrice.toString() : "");
  const [priceUnit, setPriceUnit] = useState("per_ton");
  const [includeVat, setIncludeVat] = useState(true);
  const [vatRate, setVatRate] = useState(15);
  const [quantityTons, setQuantityTons] = useState("");
  const [validUntil, setValidUntil] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().slice(0, 10);
  });
  const [paymentTerms, setPaymentTerms] = useState("");
  const [deliveryFrom, setDeliveryFrom] = useState("");
  const [deliveryTo, setDeliveryTo] = useState("");
  const [deliveryNotes, setDeliveryNotes] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [createdQuote, setCreatedQuote] = useState<{ id: string; quote_number: string } | null>(null);
  const [downloading, setDownloading] = useState(false);

  // One-off client details
  const [oneOffName, setOneOffName] = useState("");
  const [oneOffCompany, setOneOffCompany] = useState("");
  const [oneOffReg, setOneOffReg] = useState("");
  const [oneOffVat, setOneOffVat] = useState("");
  const [oneOffAddress, setOneOffAddress] = useState("");
  const [oneOffPhone, setOneOffPhone] = useState("");
  const [oneOffEmail, setOneOffEmail] = useState("");

  // Sync price when prop changes (e.g. user sets it after opening)
  useEffect(() => {
    if (sellingPrice > 0 && !price) setPrice(sellingPrice.toString());
  }, [sellingPrice]);

  const selectedCompany: CompanyProfile | null = companies[selectedCompanyIdx] || null;
  const effectiveClientName = hasExistingClient ? clientName : oneOffName;
  const parsedPrice = parseFloat(price) || 0;
  const parsedQty = parseFloat(quantityTons) || 0;

  async function handleCreate() {
    if (!selectedCompany && companies.length > 0) {
      toast.error("Select a company profile");
      return;
    }
    if (!effectiveClientName.trim()) {
      toast.error("Enter a client name");
      return;
    }
    if (parsedPrice <= 0) {
      toast.error("Enter a price");
      return;
    }
    setCreating(true);
    try {
      const clientDetails = hasExistingClient ? undefined : {
        company_name: oneOffCompany || undefined,
        reg_number: oneOffReg || undefined,
        vat_number: oneOffVat || undefined,
        address: oneOffAddress || undefined,
        phone: oneOffPhone || undefined,
        email: oneOffEmail || undefined,
      };

      const quote = await api.post<{ id: string; quote_number: string }>("/api/quotes/admin/create", {
        client_name: effectiveClientName.trim(),
        farm_name: farmName || null,
        client_id: clientId || null,
        request_data: {
          ...blendData,
          product_name: productName || blendData.sa_notation,
          quoting_company: selectedCompany,
        },
        quoted_price: parsedPrice,
        price_unit: priceUnit,
        valid_until: validUntil || null,
        admin_notes: notes || null,
        blend_id: savedBlendId || null,
        client_company_details: clientDetails || null,
        payment_terms: paymentTerms || null,
        delivery_date_from: deliveryFrom || null,
        delivery_date_to: deliveryTo || null,
        delivery_notes: deliveryNotes || null,
        quantity_tons: parsedQty > 0 ? parsedQty : null,
        include_vat: includeVat,
        vat_rate: includeVat ? vatRate : null,
      });
      setCreatedQuote(quote);
      toast.success(`Quote ${quote.quote_number} created`);
    } catch (err) {
      toast.error("Failed: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setCreating(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-4 pt-[5vh]">
      <div className="w-full max-w-3xl rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Create Quote</h2>
          <button onClick={onClose} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="size-5" />
          </button>
        </div>

        <div className="max-h-[80vh] overflow-y-auto px-6 py-5">
        <div className="grid gap-6 md:grid-cols-2">
          {/* ══ LEFT COLUMN ══ */}
          <div className="space-y-5">
          {/* ── Quote From ── */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quote From</Label>
            {companies.length === 0 ? (
              <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
                No company profiles. <a href="/profile" className="underline">Add one on Profile</a>.
              </p>
            ) : (
              <div className="space-y-2">
                {companies.map((cp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSelectedCompanyIdx(idx)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      selectedCompanyIdx === idx
                        ? "border-[var(--sapling-orange)] bg-orange-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Building2 className={`size-4 ${selectedCompanyIdx === idx ? "text-[var(--sapling-orange)]" : "text-gray-400"}`} />
                      <span className="font-medium text-[var(--sapling-dark)]">{cp.label || cp.company_name}</span>
                    </div>
                    {cp.vat_number && <p className="ml-6 text-xs text-muted-foreground">VAT: {cp.vat_number}</p>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ── Quote To ── */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quote To</Label>
            {hasExistingClient ? (
              <div className="rounded-lg bg-gray-50 p-3 text-sm">
                <p className="font-medium text-[var(--sapling-dark)]">{clientName}</p>
                {farmName && <p className="text-muted-foreground">{farmName}</p>}
              </div>
            ) : (
              <div className="space-y-3 rounded-lg border p-3">
                <div className="grid gap-1.5">
                  <Label className="text-xs">Client / Contact Name *</Label>
                  <Input value={oneOffName} onChange={(e) => setOneOffName(e.target.value)} placeholder="e.g. John Smith" />
                </div>
                <div className="grid gap-1.5">
                  <Label className="text-xs">Company Name</Label>
                  <Input value={oneOffCompany} onChange={(e) => setOneOffCompany(e.target.value)} placeholder="e.g. Smith Farming (Pty) Ltd" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1.5">
                    <Label className="text-xs">Reg Number</Label>
                    <Input value={oneOffReg} onChange={(e) => setOneOffReg(e.target.value)} />
                  </div>
                  <div className="grid gap-1.5">
                    <Label className="text-xs">VAT Number</Label>
                    <Input value={oneOffVat} onChange={(e) => setOneOffVat(e.target.value)} />
                  </div>
                </div>
                <div className="grid gap-1.5">
                  <Label className="text-xs">Address</Label>
                  <Input value={oneOffAddress} onChange={(e) => setOneOffAddress(e.target.value)} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1.5">
                    <Label className="text-xs">Phone</Label>
                    <Input value={oneOffPhone} onChange={(e) => setOneOffPhone(e.target.value)} />
                  </div>
                  <div className="grid gap-1.5">
                    <Label className="text-xs">Email</Label>
                    <Input type="email" value={oneOffEmail} onChange={(e) => setOneOffEmail(e.target.value)} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── Notes (left column) ── */}
          <div className="space-y-1.5">
            <Label className="text-xs">Internal Notes</Label>
            <textarea
              className="w-full rounded-md border bg-white px-3 py-2 text-sm"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Not shown on PDF..."
            />
          </div>

          </div>
          {/* ══ RIGHT COLUMN ══ */}
          <div className="space-y-5">

          {/* ── Product ── */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Product</Label>
            <div className="grid gap-1.5">
              <Label className="text-xs">Product Name</Label>
              <Input
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder={blendData.sa_notation || "Custom product name"}
              />
            </div>
            <div className="rounded-lg bg-gray-50 p-3 text-sm">
              <p className="text-muted-foreground">{blendData.international_notation} &middot; {blendData.batch_size}kg batch</p>
            </div>
          </div>

          {/* ── Pricing ── */}
          <div className="space-y-3">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Pricing</Label>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 grid gap-1.5">
                <Label className="text-xs">Price (R) *</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="e.g. 6500"
                  className="text-lg font-bold"
                />
              </div>
              <div className="grid gap-1.5">
                <Label className="text-xs">Unit</Label>
                <select
                  value={priceUnit}
                  onChange={(e) => setPriceUnit(e.target.value)}
                  className="rounded-md border bg-white px-3 py-2 text-sm"
                >
                  <option value="per_ton">per ton</option>
                  <option value="per_ha">per ha</option>
                  <option value="per_bag">per bag</option>
                  <option value="total">total</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label className="text-xs">Quantity (tons)</Label>
                <Input type="number" step="0.1" value={quantityTons} onChange={(e) => setQuantityTons(e.target.value)} placeholder="Optional" />
              </div>
              <div className="grid gap-1.5">
                <Label className="text-xs">Valid Until</Label>
                <Input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
              </div>
            </div>
            {/* VAT toggle */}
            <div className="flex items-center gap-3">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeVat}
                  onChange={(e) => setIncludeVat(e.target.checked)}
                  className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                />
                <span className="text-xs">Include VAT</span>
              </label>
              {includeVat && (
                <div className="flex items-center gap-1">
                  <Input
                    type="number"
                    className="w-16 text-xs"
                    value={vatRate}
                    onChange={(e) => setVatRate(parseFloat(e.target.value) || 0)}
                  />
                  <span className="text-xs text-muted-foreground">%</span>
                </div>
              )}
            </div>
            {/* Price summary */}
            {parsedPrice > 0 && (
              <div className="rounded-lg border bg-gray-50 p-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Price excl. VAT</span>
                  <span className="font-medium">R {parsedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                {includeVat && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">VAT ({vatRate}%)</span>
                      <span className="font-medium">R {(parsedPrice * vatRate / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                    <div className="mt-1 flex justify-between border-t pt-1 font-semibold text-[var(--sapling-dark)]">
                      <span>Price incl. VAT</span>
                      <span>R {(parsedPrice * (1 + vatRate / 100)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </>
                )}
                {parsedQty > 0 && priceUnit === "per_ton" && (
                  <div className="mt-2 flex justify-between border-t pt-1 font-semibold text-green-700">
                    <span>Total ({parsedQty} tons)</span>
                    <span>R {(parsedPrice * (includeVat ? (1 + vatRate / 100) : 1) * parsedQty).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Terms & Delivery ── */}
          <div className="space-y-3">
            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Terms & Delivery</Label>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label className="text-xs">Payment Terms</Label>
                <select
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                  className="rounded-md border bg-white px-3 py-2 text-sm"
                >
                  <option value="">Not specified</option>
                  <option value="payment_at_order">Payment at order</option>
                  <option value="payment_on_delivery">Payment on delivery</option>
                  <option value="30_days">30 days</option>
                  <option value="60_days">60 days</option>
                </select>
              </div>
              <div className="grid gap-1.5">
                <Label className="text-xs">Delivery Notes</Label>
                <Input value={deliveryNotes} onChange={(e) => setDeliveryNotes(e.target.value)} placeholder="Collection / address..." />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label className="text-xs">Delivery From</Label>
                <Input type="date" value={deliveryFrom} onChange={(e) => setDeliveryFrom(e.target.value)} />
              </div>
              <div className="grid gap-1.5">
                <Label className="text-xs">Delivery To</Label>
                <Input type="date" value={deliveryTo} onChange={(e) => setDeliveryTo(e.target.value)} />
              </div>
            </div>
          </div>

          </div>
          {/* ══ END COLUMNS ══ */}
          </div>

          {/* ── Actions ── */}
          {createdQuote ? (
            <div className="space-y-3 border-t pt-4">
              <div className="flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm font-medium text-green-700">
                <Check className="size-4" />
                Quote {createdQuote.quote_number} created
              </div>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={async () => {
                    setDownloading(true);
                    try {
                      const session = await (await import("@/lib/supabase")).createClient().auth.getSession();
                      const token = session.data.session?.access_token;
                      const res = await fetch(
                        `${(await import("@/lib/api")).API_URL}/api/quotes/${createdQuote.id}/pdf`,
                        { headers: { Authorization: `Bearer ${token}` } }
                      );
                      if (!res.ok) throw new Error("PDF download failed");
                      const blob = await res.blob();
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `Quote_${createdQuote.quote_number}.pdf`;
                      a.click();
                      URL.revokeObjectURL(url);
                    } catch (err) {
                      toast.error(err instanceof Error ? err.message : "Download failed");
                    } finally {
                      setDownloading(false);
                    }
                  }}
                  disabled={downloading}
                  className="flex-1"
                >
                  {downloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                  Download PDF
                </Button>
                <Button
                  onClick={() => { setCreatedQuote(null); onClose(); }}
                  className="flex-1 bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  Done
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex gap-3 border-t pt-4">
              <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
              <Button
                onClick={handleCreate}
                disabled={creating}
                className="flex-1 bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {creating ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                Create Quote
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
