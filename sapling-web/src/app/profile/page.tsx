"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth, getCompanyProfiles } from "@/lib/auth-context";
import type { CompanyProfile } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { toast } from "sonner";
import { Pencil, Plus, RotateCcw, X, Save } from "lucide-react";

interface CropRequirement {
  crop: string;
  type?: string;
  yield_unit?: string;
  default_yield?: number;
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
  c?: number;
}

interface CropOverride {
  crop: string;
  agent_id: string;
  n?: number | null;
  p?: number | null;
  k?: number | null;
  ca?: number | null;
  mg?: number | null;
  s?: number | null;
  fe?: number | null;
  b?: number | null;
  mn?: number | null;
  zn?: number | null;
  mo?: number | null;
  cu?: number | null;
  c?: number | null;
}

const NUTRIENT_FIELDS = [
  "n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu",
] as const;

interface ContactForm {
  name: string;
  phone: string;
  company: string;
}

interface CompanyForm {
  label: string;
  company_name: string;
  reg_number: string;
  vat_number: string;
  address: string;
  phone: string;
  email: string;
  website: string;
}

const EMPTY_COMPANY: CompanyForm = {
  label: "", company_name: "", reg_number: "", vat_number: "",
  address: "", phone: "", email: "", website: "",
};

export default function ProfilePage() {
  const { profile, isLoading: authLoading } = useAuth();

  // Contact info
  const [contactForm, setContactForm] = useState<ContactForm>({
    name: "",
    phone: "",
    company: "",
  });
  const [contactEditing, setContactEditing] = useState(false);
  const [contactSaving, setContactSaving] = useState(false);

  // Company profiles (multiple). -1 = adding new, null = not editing
  const [companyProfiles, setCompanyProfiles] = useState<CompanyForm[]>([]);
  const [editingCompanyIdx, setEditingCompanyIdx] = useState<number | null>(null);
  const [companyForm, setCompanyForm] = useState<CompanyForm>({ ...EMPTY_COMPANY });
  const [companySaving, setCompanySaving] = useState(false);

  // Crop overrides
  const [crops, setCrops] = useState<CropRequirement[]>([]);
  const [overrides, setOverrides] = useState<CropOverride[]>([]);
  const [loadingCrops, setLoadingCrops] = useState(true);

  // Override edit dialog
  const [editCrop, setEditCrop] = useState<string | null>(null);
  const [overrideForm, setOverrideForm] = useState<Record<string, number | string>>({});
  const [overrideSaving, setOverrideSaving] = useState(false);
  const [resetting, setResetting] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      setContactForm({
        name: profile.name,
        phone: profile.phone ?? "",
        company: profile.company ?? "",
      });
      const profiles = getCompanyProfiles(profile);
      if (profiles.length > 0) {
        setCompanyProfiles(profiles.map((p) => ({
          label: p.label || p.company_name || "",
          company_name: p.company_name || "",
          reg_number: p.reg_number || "",
          vat_number: p.vat_number || "",
          address: p.address || "",
          phone: p.phone || "",
          email: p.email || "",
          website: p.website || "",
        })));
      } else {
        setCompanyProfiles([]);
      }
    }
  }, [profile]);

  const fetchCropData = useCallback(async () => {
    try {
      setLoadingCrops(true);
      const [cropsData, overridesData] = await Promise.all([
        api.get<CropRequirement[]>("/api/crop-norms"),
        api.get<CropOverride[]>("/api/crop-norms/overrides"),
      ]);
      setCrops(cropsData);
      setOverrides(overridesData);
    } catch (err) {
      toast.error("Failed to load crop data");
    } finally {
      setLoadingCrops(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && profile) {
      fetchCropData();
    }
  }, [authLoading, profile, fetchCropData]);

  async function saveContact() {
    setContactSaving(true);
    try {
      await api.patch(`/api/admin/users/${profile!.id}`, {
        name: contactForm.name,
        phone: contactForm.phone || null,
        company: contactForm.company || null,
      });
      toast.success("Profile updated");
      setContactEditing(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    } finally {
      setContactSaving(false);
    }
  }

  function openCompanyEditor(idx: number) {
    if (idx >= 0 && companyProfiles[idx]) {
      setCompanyForm({ ...companyProfiles[idx] });
    } else {
      setCompanyForm({ ...EMPTY_COMPANY });
    }
    setEditingCompanyIdx(idx);
  }

  async function saveCompanyProfile() {
    setCompanySaving(true);
    try {
      const updated = [...companyProfiles];
      const clean: Record<string, string> = {};
      for (const [k, v] of Object.entries(companyForm)) {
        if (v) clean[k] = v;
      }
      if (!clean.label) clean.label = clean.company_name || "Company";
      if (editingCompanyIdx !== null && editingCompanyIdx >= 0 && editingCompanyIdx < updated.length) {
        updated[editingCompanyIdx] = companyForm;
      } else {
        updated.push(companyForm);
      }
      await api.patch(`/api/admin/users/${profile!.id}`, {
        company: updated[0]?.company_name || null,
        company_details: updated.map((p) => {
          const o: Record<string, string> = {};
          for (const [k, v] of Object.entries(p)) { if (v) o[k] = v; }
          if (!o.label) o.label = o.company_name || "Company";
          return o;
        }),
      });
      setCompanyProfiles(updated);
      toast.success("Company profile saved");
      setEditingCompanyIdx(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setCompanySaving(false);
    }
  }

  async function deleteCompanyProfile(idx: number) {
    if (!confirm("Remove this company profile?")) return;
    const updated = companyProfiles.filter((_, i) => i !== idx);
    try {
      await api.patch(`/api/admin/users/${profile!.id}`, {
        company: updated[0]?.company_name || null,
        company_details: updated.length > 0 ? updated : null,
      });
      setCompanyProfiles(updated);
      toast.success("Company profile removed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Remove failed");
    }
  }

  function openOverrideEdit(crop: string) {
    const existing = overrides.find((o) => o.crop === crop);
    const defaults = crops.find((c) => c.crop === crop);
    const form: Record<string, number | string> = {};
    for (const field of NUTRIENT_FIELDS) {
      const overrideVal = existing?.[field];
      form[field] = overrideVal != null ? overrideVal : (defaults?.[field] ?? 0);
    }
    setOverrideForm(form);
    setEditCrop(crop);
  }

  async function saveOverride() {
    if (!editCrop) return;
    setOverrideSaving(true);
    try {
      const body: Record<string, number> = {};
      for (const field of NUTRIENT_FIELDS) {
        const val = parseFloat(String(overrideForm[field]));
        if (!isNaN(val)) body[field] = val;
      }
      await api.put(`/api/crop-norms/overrides/${encodeURIComponent(editCrop)}`, body);
      toast.success(`Override saved for ${editCrop}`);
      setEditCrop(null);
      fetchCropData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setOverrideSaving(false);
    }
  }

  async function resetOverride(crop: string) {
    setResetting(crop);
    try {
      await api.delete(`/api/crop-norms/overrides/${encodeURIComponent(crop)}`);
      toast.success(`Reset ${crop} to defaults`);
      fetchCropData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setResetting(null);
    }
  }

  function hasOverride(crop: string): boolean {
    return overrides.some((o) => o.crop === crop);
  }

  if (authLoading) return null;

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Profile</h1>
        <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
          Manage your account and crop norm preferences
        </p>

        {/* Contact Info Card */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
            <CardDescription>Your account details</CardDescription>
          </CardHeader>
          <CardContent>
            {contactEditing ? (
              <div className="grid gap-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="p-name">Name</Label>
                  <Input
                    id="p-name"
                    value={contactForm.name}
                    onChange={(e) =>
                      setContactForm((f) => ({ ...f, name: e.target.value }))
                    }
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label>Email</Label>
                  <p className="text-sm text-gray-500">{profile?.email}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-1.5">
                    <Label htmlFor="p-phone">Phone</Label>
                    <Input
                      id="p-phone"
                      value={contactForm.phone}
                      onChange={(e) =>
                        setContactForm((f) => ({ ...f, phone: e.target.value }))
                      }
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label htmlFor="p-company">Company</Label>
                    <Input
                      id="p-company"
                      value={contactForm.company}
                      onChange={(e) =>
                        setContactForm((f) => ({ ...f, company: e.target.value }))
                      }
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={saveContact} disabled={contactSaving}>
                    <Save className="size-4" data-icon="inline-start" />
                    {contactSaving ? "Saving..." : "Save"}
                  </Button>
                  <Button variant="outline" onClick={() => setContactEditing(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid gap-3">
                <div className="flex justify-between">
                  <div className="grid gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Name: </span>
                      <span className="font-medium text-[var(--sapling-dark)]">
                        {profile?.name}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Email: </span>
                      <span className="font-medium text-[var(--sapling-dark)]">
                        {profile?.email}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Phone: </span>
                      <span className="font-medium text-[var(--sapling-dark)]">
                        {profile?.phone ?? "-"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Company: </span>
                      <span className="font-medium text-[var(--sapling-dark)]">
                        {profile?.company ?? "-"}
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setContactEditing(true)}
                  >
                    <Pencil className="size-3.5" data-icon="inline-start" />
                    Edit
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Company Profiles Card */}
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Company Profiles</CardTitle>
                <CardDescription>
                  Your company details appear on quotes and PDFs. Add multiple if you quote from different entities.
                </CardDescription>
              </div>
              {editingCompanyIdx === null && (
                <Button variant="outline" size="sm" onClick={() => openCompanyEditor(-1)}>
                  <Plus className="size-3.5" data-icon="inline-start" />
                  Add Company
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {editingCompanyIdx !== null ? (
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-1.5">
                    <Label>Label (for selection)</Label>
                    <Input value={companyForm.label} onChange={(e) => setCompanyForm((f) => ({ ...f, label: e.target.value }))} placeholder="e.g. Sapling Fertilizer" />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Company Name</Label>
                    <Input value={companyForm.company_name} onChange={(e) => setCompanyForm((f) => ({ ...f, company_name: e.target.value }))} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-1.5">
                    <Label>Registration Number</Label>
                    <Input value={companyForm.reg_number} onChange={(e) => setCompanyForm((f) => ({ ...f, reg_number: e.target.value }))} placeholder="e.g. 2024/123456/07" />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>VAT Number</Label>
                    <Input value={companyForm.vat_number} onChange={(e) => setCompanyForm((f) => ({ ...f, vat_number: e.target.value }))} placeholder="e.g. 4012345678" />
                  </div>
                </div>
                <div className="grid gap-1.5">
                  <Label>Address</Label>
                  <Input value={companyForm.address} onChange={(e) => setCompanyForm((f) => ({ ...f, address: e.target.value }))} placeholder="Street, City, Province, Code" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-1.5">
                    <Label>Phone</Label>
                    <Input value={companyForm.phone} onChange={(e) => setCompanyForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+27 ..." />
                  </div>
                  <div className="grid gap-1.5">
                    <Label>Email</Label>
                    <Input type="email" value={companyForm.email} onChange={(e) => setCompanyForm((f) => ({ ...f, email: e.target.value }))} />
                  </div>
                </div>
                <div className="grid gap-1.5">
                  <Label>Website</Label>
                  <Input value={companyForm.website} onChange={(e) => setCompanyForm((f) => ({ ...f, website: e.target.value }))} placeholder="www.example.co.za" />
                </div>
                <div className="flex gap-2">
                  <Button onClick={saveCompanyProfile} disabled={companySaving}>
                    <Save className="size-4" data-icon="inline-start" />
                    {companySaving ? "Saving..." : "Save"}
                  </Button>
                  <Button variant="outline" onClick={() => setEditingCompanyIdx(null)}>Cancel</Button>
                </div>
              </div>
            ) : companyProfiles.length === 0 ? (
              <p className="text-sm text-muted-foreground">No company profiles yet. Add one to include your details on quotes.</p>
            ) : (
              <div className="space-y-3">
                {companyProfiles.map((cp, idx) => (
                  <div key={idx} className="flex items-start justify-between rounded-lg border p-4">
                    <div className="grid gap-1 text-sm">
                      <p className="font-semibold text-[var(--sapling-dark)]">{cp.label || cp.company_name}</p>
                      {cp.company_name && cp.company_name !== cp.label && (
                        <p className="text-muted-foreground">{cp.company_name}</p>
                      )}
                      <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
                        {cp.reg_number && <span>Reg: {cp.reg_number}</span>}
                        {cp.vat_number && <span>VAT: {cp.vat_number}</span>}
                      </div>
                      {cp.address && <p className="text-xs text-muted-foreground">{cp.address}</p>}
                      <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
                        {cp.phone && <span>{cp.phone}</span>}
                        {cp.email && <span>{cp.email}</span>}
                        {cp.website && <span>{cp.website}</span>}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openCompanyEditor(idx)}>
                        <Pencil className="size-3.5" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => deleteCompanyProfile(idx)}>
                        <X className="size-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Crop Norm Overrides */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Crop Norm Overrides</CardTitle>
            <CardDescription>
              Customize crop nutrient requirements. Overrides only affect your calculations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingCrops ? (
              <div className="flex justify-center py-8">
                <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-[var(--sapling-orange)]" />
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-4 py-3">Crop</th>
                      <th className="px-4 py-3 text-right">N</th>
                      <th className="px-4 py-3 text-right">P</th>
                      <th className="px-4 py-3 text-right">K</th>
                      <th className="px-4 py-3 text-right">Ca</th>
                      <th className="px-4 py-3 text-right">Mg</th>
                      <th className="px-4 py-3 text-right">S</th>
                      <th className="px-4 py-3 text-center">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {crops.map((crop) => {
                      const isOverridden = hasOverride(crop.crop);
                      return (
                        <tr key={crop.crop} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-[var(--sapling-dark)]">
                            {crop.crop}
                          </td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.n}</td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.p}</td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.k}</td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.ca}</td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.mg}</td>
                          <td className="px-4 py-3 text-right tabular-nums">{crop.s}</td>
                          <td className="px-4 py-3 text-center">
                            {isOverridden ? (
                              <span className="inline-flex rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                                Custom
                              </span>
                            ) : (
                              <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                                Default
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="outline"
                                size="xs"
                                onClick={() => openOverrideEdit(crop.crop)}
                              >
                                Customize
                              </Button>
                              {isOverridden && (
                                <Button
                                  variant="ghost"
                                  size="icon-xs"
                                  disabled={resetting === crop.crop}
                                  onClick={() => resetOverride(crop.crop)}
                                  title="Reset to Default"
                                >
                                  <RotateCcw className="size-3.5" />
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {crops.length === 0 && (
                      <tr>
                        <td colSpan={9} className="px-4 py-8 text-center text-gray-400">
                          No crops found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Override Edit Dialog */}
      {editCrop && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
                Customize: {editCrop}
              </h2>
              <Button variant="ghost" size="icon-xs" onClick={() => setEditCrop(null)}>
                <X className="size-4" />
              </Button>
            </div>

            <p className="mt-1 text-sm text-gray-500">
              Set your custom nutrient requirements (kg/ha)
            </p>

            <div className="mt-4 grid grid-cols-3 gap-3">
              {NUTRIENT_FIELDS.map((field) => (
                <div key={field} className="grid gap-1">
                  <Label htmlFor={`ov-${field}`} className="text-xs uppercase">
                    {field}
                  </Label>
                  <Input
                    id={`ov-${field}`}
                    type="number"
                    step="0.01"
                    value={overrideForm[field] ?? 0}
                    onChange={(e) =>
                      setOverrideForm((prev) => ({
                        ...prev,
                        [field]: e.target.value,
                      }))
                    }
                  />
                </div>
              ))}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditCrop(null)}>
                Cancel
              </Button>
              <Button onClick={saveOverride} disabled={overrideSaving}>
                {overrideSaving ? "Saving..." : "Save Override"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
