"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { usePagination } from "@/lib/use-pagination";
import { PaginationControls } from "@/components/pagination-controls";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Users,
  Search,
  Plus,
  Loader2,
  X,
  Phone,
  Mail,
  User,
  MapPin,
  Layers,
  Trash2,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface Client {
  id: string;
  name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  company_details: { name?: string; [key: string]: unknown } | null;
  agent_id: string;
  // Server-computed aggregates from GET /api/clients/ list
  // (fallback 0 if an older backend without these fields is hit).
  farm_count?: number;
  field_count?: number;
}

interface Farm {
  id: string;
  client_id: string;
  name: string;
}

interface Field {
  id: string;
  farm_id: string;
  name: string;
}

// ── Dialog ─────────────────────────────────────────────────────────────────

function Dialog({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">{title}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

export default function ClientsPageWrapper() {
  return (
    <Suspense>
      <ClientsPage />
    </Suspense>
  );
}

function ClientsPage() {
  // Server-side pagination + search (backend `/api/clients/?search=...&skip=&limit=`).
  // URL query params are synced so the view is shareable / back-button friendly.
  const pagination = usePagination<Client>({
    basePath: "/api/clients/",
  });
  const clients = pagination.page?.items ?? [];
  const loading = pagination.loading;
  const search = pagination.params.search ?? "";

  const [farmCounts, setFarmCounts] = useState<Record<string, number>>({});
  const [fieldCounts, setFieldCounts] = useState<Record<string, number>>({});

  // Add client dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formName, setFormName] = useState("");
  const [formCompany, setFormCompany] = useState("");
  const [formContact, setFormContact] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formNotes, setFormNotes] = useState("");

  const resetForm = () => {
    setFormName("");
    setFormCompany("");
    setFormContact("");
    setFormEmail("");
    setFormPhone("");
    setFormNotes("");
  };

  // Server now returns farm_count + field_count directly on each
  // client row (GET /api/clients/ enrichment). The old N+1 fan-out
  // was flooding the Supabase HTTP/2 pool and producing CORS-looking
  // 500s that silently left every card showing "0 farms 0 fields."
  useEffect(() => {
    if (!clients.length) {
      setFarmCounts({});
      setFieldCounts({});
      return;
    }
    const fc: Record<string, number> = {};
    const flc: Record<string, number> = {};
    for (const c of clients) {
      fc[c.id] = c.farm_count ?? 0;
      flc[c.id] = c.field_count ?? 0;
    }
    setFarmCounts(fc);
    setFieldCounts(flc);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clients.map((c) => c.id).join(",")]);

  const handleSaveClient = async () => {
    if (!formName.trim()) {
      toast.error("Client name is required");
      return;
    }
    setSaving(true);
    try {
      await api.post("/api/clients", {
        name: formName.trim(),
        contact_person: formContact || null,
        email: formEmail || null,
        phone: formPhone || null,
        notes: formNotes || null,
        company_details: formCompany ? { name: formCompany } : null,
      });
      setDialogOpen(false);
      resetForm();
      toast.success("Client created");
      pagination.refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create client");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (!confirm(`Are you sure you want to delete "${clientName}"?`)) return;
    try {
      await api.delete(`/api/clients/${clientId}`);
      toast.success(`"${clientName}" deleted`);
      pagination.refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete client");
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
              <Users className="size-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Clients</h1>
              <p className="text-sm text-[var(--sapling-medium-grey)]">
                {pagination.page?.total ?? 0} client
                {(pagination.page?.total ?? 0) !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <Button
            onClick={() => { resetForm(); setDialogOpen(true); }}
            className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
          >
            <Plus className="size-4" />
            Add Client
          </Button>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => pagination.setSearch(e.target.value)}
            placeholder="Search by name, company, contact or email..."
            className="pl-9"
          />
        </div>

        {/* Loading skeleton — three placeholder cards in the same
            grid layout so the page doesn't jump on first paint. */}
        {loading && clients.length === 0 ? (
          <div
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-busy="true"
            aria-label="Loading clients"
          >
            {[0, 1, 2].map((i) => (
              <div key={i} className="animate-pulse rounded-lg border bg-white p-4">
                <div className="h-4 w-3/4 rounded bg-muted" />
                <div className="mt-2 h-3 w-1/2 rounded bg-muted/70" />
                <div className="mt-4 flex gap-2">
                  <div className="h-3 w-12 rounded bg-muted/70" />
                  <div className="h-3 w-12 rounded bg-muted/70" />
                </div>
              </div>
            ))}
          </div>
        ) : clients.length === 0 ? (
          <div className="py-12 text-center">
            <Users className="mx-auto size-8 text-gray-300" />
            <h3 className="mt-3 font-semibold text-[var(--sapling-dark)]">
              {search ? "No clients match your search" : "No clients yet"}
            </h3>
            {!search && (
              <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
                Add your first client to get started.
              </p>
            )}
          </div>
        ) : (
          /* Card grid */
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {clients.map((client) => (
              <Link
                key={client.id}
                href={`/clients/${client.id}`}
                className="group rounded-xl border bg-white p-5 transition-all hover:border-[var(--sapling-orange)]/40 hover:shadow-md no-underline"
              >
                {/* Name + company */}
                <h3 className="text-lg font-semibold text-[var(--sapling-dark)] group-hover:text-[var(--sapling-orange)]">
                  {client.name}
                </h3>
                {client.company_details?.name && (
                  <p className="mt-0.5 text-sm text-[var(--sapling-medium-grey)]">
                    {String(client.company_details.name)}
                  </p>
                )}

                {/* Contact details */}
                <div className="mt-3 space-y-1">
                  {client.contact_person && (
                    <div className="flex items-center gap-2 text-xs text-[var(--sapling-medium-grey)]">
                      <User className="size-3 shrink-0" />
                      <span>{client.contact_person}</span>
                    </div>
                  )}
                  {client.email && (
                    <div className="flex items-center gap-2 text-xs text-[var(--sapling-medium-grey)]">
                      <Mail className="size-3 shrink-0" />
                      <span className="truncate">{client.email}</span>
                    </div>
                  )}
                  {client.phone && (
                    <div className="flex items-center gap-2 text-xs text-[var(--sapling-medium-grey)]">
                      <Phone className="size-3 shrink-0" />
                      <span>{client.phone}</span>
                    </div>
                  )}
                </div>

                {/* Stats + Delete */}
                <div className="mt-4 flex items-center justify-between border-t pt-3">
                  <div className="flex gap-4">
                    <div className="flex items-center gap-1.5 text-xs text-[var(--sapling-medium-grey)]">
                      <MapPin className="size-3" />
                      <span className="font-medium text-[var(--sapling-dark)]">{farmCounts[client.id] ?? 0}</span> farm{(farmCounts[client.id] ?? 0) !== 1 ? "s" : ""}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-[var(--sapling-medium-grey)]">
                      <Layers className="size-3" />
                      <span className="font-medium text-[var(--sapling-dark)]">{fieldCounts[client.id] ?? 0}</span> field{(fieldCounts[client.id] ?? 0) !== 1 ? "s" : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDeleteClient(client.id, client.name);
                    }}
                    className="rounded-md p-1.5 text-gray-400 opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                    title="Delete client"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination controls (shown once there are results) */}
        {!loading && clients.length > 0 && (
          <div className="mt-6">
            <PaginationControls pagination={pagination} />
          </div>
        )}
      </div>

      {/* Add Client Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} title="Add Client">
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Client Name *</Label>
            <Input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="e.g. John Smith" autoFocus />
          </div>
          <div className="space-y-1.5">
            <Label>Company Name</Label>
            <Input value={formCompany} onChange={(e) => setFormCompany(e.target.value)} placeholder="e.g. Smith Farming (Pty) Ltd" />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Contact Person</Label>
              <Input value={formContact} onChange={(e) => setFormContact(e.target.value)} placeholder="Optional" />
            </div>
            <div className="space-y-1.5">
              <Label>Phone</Label>
              <Input value={formPhone} onChange={(e) => setFormPhone(e.target.value)} placeholder="e.g. 082 123 4567" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input type="email" value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="e.g. john@smithfarm.co.za" />
          </div>
          <div className="space-y-1.5">
            <Label>Notes</Label>
            <Input value={formNotes} onChange={(e) => setFormNotes(e.target.value)} placeholder="Optional" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleSaveClient}
              disabled={saving || !formName.trim()}
              className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {saving && <Loader2 className="size-4 animate-spin" />}
              Create Client
            </Button>
          </div>
        </div>
      </Dialog>
    </AppShell>
  );
}
