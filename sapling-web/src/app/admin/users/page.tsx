"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, X, Eye } from "lucide-react";
import { startImpersonation } from "@/components/impersonation-banner";

interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  phone: string | null;
  company: string | null;
  status?: string;
  created_at?: string;
}

interface CreateForm {
  name: string;
  email: string;
  role: string;
  phone: string;
  company: string;
}

interface EditForm {
  name: string;
  role: string;
  phone: string;
  company: string;
}

const emptyCreateForm: CreateForm = {
  name: "",
  email: "",
  role: "sales_agent",
  phone: "",
  company: "",
};

const ROLES = ["admin", "sales_agent"];

export default function UsersPage() {
  const { isAdmin, isLoading: authLoading, profile } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>(emptyCreateForm);
  const [creating, setCreating] = useState(false);

  // Edit dialog
  const [editUser, setEditUser] = useState<UserProfile | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({ name: "", role: "", phone: "", company: "" });
  const [updating, setUpdating] = useState(false);

  // Delete confirm
  const [deleteUser, setDeleteUser] = useState<UserProfile | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Deactivate dialog
  const [deactivateUser, setDeactivateUser] = useState<UserProfile | null>(null);
  const [reassignTo, setReassignTo] = useState("");
  const [deactivating, setDeactivating] = useState(false);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getAll<UserProfile>("/api/admin/users");
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
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
      fetchUsers();
    }
  }, [authLoading, isAdmin, router, fetchUsers]);

  async function handleCreate() {
    if (!createForm.name.trim()) { toast.error("Name is required"); return; }
    if (!createForm.email.includes("@")) { toast.error("Valid email is required"); return; }
    // No password needed — invite email will be sent

    setCreating(true);
    try {
      const body: Record<string, string | null> = {
        name: createForm.name.trim(),
        email: createForm.email.trim(),
        role: createForm.role,
        phone: createForm.phone || null,
        company: createForm.company || null,
      };
      await api.post("/api/admin/users", body);
      toast.success("Invite sent! They will receive an email to set their password.");
      setCreateOpen(false);
      setCreateForm(emptyCreateForm);
      fetchUsers();
    } catch (err) {
      const msg = err instanceof Error ? err.message : typeof err === "string" ? err : "Create failed — email may already exist";
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  }

  function openEdit(u: UserProfile) {
    setEditUser(u);
    setEditForm({
      name: u.name,
      role: u.role,
      phone: u.phone ?? "",
      company: u.company ?? "",
    });
  }

  async function handleUpdate() {
    if (!editUser) return;
    setUpdating(true);
    try {
      const body: Record<string, string | null> = {
        name: editForm.name,
        role: editForm.role,
        phone: editForm.phone || null,
        company: editForm.company || null,
      };
      await api.patch(`/api/admin/users/${editUser.id}`, body);
      toast.success("User updated");
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : typeof err === "string" ? err : "Update failed");
    } finally {
      setUpdating(false);
    }
  }

  async function handleDelete() {
    if (!deleteUser) return;
    setDeleting(true);
    try {
      await api.delete(`/api/admin/users/${deleteUser.id}`);
      toast.success("User deleted");
      setDeleteUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : typeof err === "string" ? err : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  async function handleDeactivate() {
    if (!deactivateUser) return;
    setDeactivating(true);
    try {
      await api.post(`/api/admin/users/${deactivateUser.id}/deactivate`, {
        reassign_to: reassignTo || null,
      });
      toast.success(`${deactivateUser.name} has been deactivated${reassignTo ? " and data reassigned" : ""}`);
      setDeactivateUser(null);
      setReassignTo("");
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Deactivation failed");
    } finally {
      setDeactivating(false);
    }
  }

  async function handleReactivate(u: UserProfile) {
    try {
      await api.post(`/api/admin/users/${u.id}/reactivate`, {});
      toast.success(`${u.name} has been reactivated`);
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Reactivation failed");
    }
  }

  if (authLoading) return null;

  return (
    <>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Users</h1>
            <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
              Manage user accounts and roles
            </p>
          </div>
          <Button onClick={() => { setCreateForm(emptyCreateForm); setCreateOpen(true); }}>
            <Plus className="size-4" data-icon="inline-start" />
            Create User
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
          <div className="mt-6 overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Phone</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((u) => {
                  const isInactive = u.status === "inactive";
                  return (
                    <tr key={u.id || u.email || u.name} className={`hover:bg-gray-50 ${isInactive ? "opacity-60" : ""}`}>
                      <td className="px-4 py-3 font-medium text-[var(--sapling-dark)]">
                        {u.name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{u.email}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            u.role === "admin"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            isInactive
                              ? "bg-red-100 text-red-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {isInactive ? "Inactive" : "Active"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{u.phone ?? "-"}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {!isInactive && u.id !== profile?.id && (
                            <Button
                              variant="outline"
                              size="xs"
                              onClick={() => {
                                startImpersonation({
                                  id: u.id,
                                  name: u.name,
                                  email: u.email,
                                  role: u.role,
                                });
                                window.location.href = "/";
                              }}
                              title="View as this user"
                            >
                              <Eye className="size-3.5" />
                              View as
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon-xs"
                            onClick={() => openEdit(u)}
                          >
                            <Pencil className="size-3.5" />
                          </Button>
                          {isInactive ? (
                            <Button
                              variant="outline"
                              size="xs"
                              onClick={() => handleReactivate(u)}
                            >
                              Reactivate
                            </Button>
                          ) : (
                            <Button
                              variant="destructive"
                              size="xs"
                              disabled={u.id === profile?.id}
                              onClick={() => {
                                setDeactivateUser(u);
                                setReassignTo("");
                              }}
                            >
                              Deactivate
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                      No users found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User Dialog */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Create User</h2>
              <Button variant="ghost" size="icon-xs" onClick={() => setCreateOpen(false)}>
                <X className="size-4" />
              </Button>
            </div>

            <div className="mt-4 grid gap-4">
              <div className="grid gap-1.5">
                <Label htmlFor="c-name">Name</Label>
                <Input
                  id="c-name"
                  value={createForm.name}
                  onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="c-email">Email</Label>
                <Input
                  id="c-email"
                  type="email"
                  value={createForm.email}
                  onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="c-role">Role</Label>
                <select
                  id="c-role"
                  className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                  value={createForm.role}
                  onChange={(e) => setCreateForm((f) => ({ ...f, role: e.target.value }))}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="c-phone">Phone</Label>
                  <Input
                    id="c-phone"
                    value={createForm.phone}
                    onChange={(e) => setCreateForm((f) => ({ ...f, phone: e.target.value }))}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="c-company">Company</Label>
                  <Input
                    id="c-company"
                    value={createForm.company}
                    onChange={(e) => setCreateForm((f) => ({ ...f, company: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={creating || !createForm.name || !createForm.email}
              >
                {creating ? "Sending invite..." : "Send Invite"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Dialog */}
      {editUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Edit User</h2>
              <Button variant="ghost" size="icon-xs" onClick={() => setEditUser(null)}>
                <X className="size-4" />
              </Button>
            </div>

            <p className="mt-1 text-sm text-gray-500">{editUser.email}</p>

            <div className="mt-4 grid gap-4">
              <div className="grid gap-1.5">
                <Label htmlFor="e-name">Name</Label>
                <Input
                  id="e-name"
                  value={editForm.name}
                  onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="e-role">Role</Label>
                <select
                  id="e-role"
                  className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                  value={editForm.role}
                  onChange={(e) => setEditForm((f) => ({ ...f, role: e.target.value }))}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-1.5">
                  <Label htmlFor="e-phone">Phone</Label>
                  <Input
                    id="e-phone"
                    value={editForm.phone}
                    onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="e-company">Company</Label>
                  <Input
                    id="e-company"
                    value={editForm.company}
                    onChange={(e) => setEditForm((f) => ({ ...f, company: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditUser(null)}>
                Cancel
              </Button>
              <Button onClick={handleUpdate} disabled={updating || !editForm.name}>
                {updating ? "Updating..." : "Update"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">Delete User</h2>
            <p className="mt-2 text-sm text-gray-600">
              Are you sure you want to delete <strong>{deleteUser.name}</strong> ({deleteUser.email})?
              This action cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteUser(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Deactivate User Dialog */}
      {deactivateUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-[var(--sapling-dark)]">
              Deactivate {deactivateUser.name}
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              This will disable their login. Their profile and name will remain visible on historical records.
            </p>

            <div className="mt-4 rounded-lg border border-orange-200 bg-orange-50 p-3">
              <p className="text-sm font-medium text-orange-800">
                Reassign data (optional)
              </p>
              <p className="mt-1 text-xs text-orange-700">
                Transfer this agent's clients, soil analyses, blends, and feeding plans to another user.
                If you don't reassign, the data stays with the deactivated profile.
              </p>
              <select
                className="mt-2 h-8 w-full rounded-md border border-input bg-white px-2.5 text-sm"
                value={reassignTo}
                onChange={(e) => setReassignTo(e.target.value)}
              >
                <option value="">Don't reassign (keep with deactivated user)</option>
                {users
                  .filter((u) => u.id !== deactivateUser.id && u.status !== "inactive")
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.role})
                    </option>
                  ))}
              </select>
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeactivateUser(null)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeactivate} disabled={deactivating}>
                {deactivating ? "Deactivating..." : "Deactivate User"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
