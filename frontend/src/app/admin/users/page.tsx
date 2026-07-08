"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchCurrentUser,
  fetchAllUsers,
  approveUser,
  rejectUser,
  setUserActive,
  setUserRole,
  AuthUser,
} from "@/lib/api";

const ROLES = ["viewer", "analyst", "org_admin", "super_admin"] as const;

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  org_admin: "Org Admin",
  analyst: "Analyst",
  viewer: "Viewer",
};

const ROLE_BADGE: Record<string, string> = {
  super_admin: "bg-purple-100 text-purple-700",
  org_admin: "bg-blue-100 text-blue-700",
  analyst: "bg-teal-100 text-teal-700",
  viewer: "bg-slate-100 text-slate-600",
};

function fmtDate(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${accent}`}>{value}</p>
    </div>
  );
}

export default function AdminUsersPage() {
  const router = useRouter();
  const [me, setMe] = useState<AuthUser | null>(null);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");

  const loadUsers = useCallback(async () => {
    const list = await fetchAllUsers();
    setUsers(list);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("aic_token");
    if (!token) {
      router.replace("/login?next=/admin/users");
      return;
    }
    (async () => {
      try {
        const user = await fetchCurrentUser();
        if (user.role !== "super_admin" && user.role !== "org_admin") {
          router.replace("/dashboard");
          return;
        }
        setMe(user);
        await loadUsers();
      } catch {
        router.replace("/login?next=/admin/users");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, loadUsers]);

  async function withBusy(id: string, action: () => Promise<void>, failMsg: string) {
    setBusyId(id);
    setError(null);
    try {
      await action();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? failMsg);
    } finally {
      setBusyId(null);
    }
  }

  const pending = users.filter((u) => !u.is_verified);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return users.filter((u) => {
      if (roleFilter && u.role !== roleFilter) return false;
      if (q && !u.full_name.toLowerCase().includes(q) && !u.email.toLowerCase().includes(q))
        return false;
      return true;
    });
  }, [users, search, roleFilter]);

  const stats = useMemo(
    () => ({
      total: users.length,
      pending: users.filter((u) => !u.is_verified).length,
      active: users.filter((u) => u.is_active && u.is_verified).length,
      admins: users.filter((u) => u.role === "super_admin" || u.role === "org_admin").length,
    }),
    [users]
  );

  // org_admins cannot modify super_admin accounts, and nobody edits themselves here.
  const canManage = (u: AuthUser) =>
    u.id !== me?.id && (me?.role === "super_admin" || u.role !== "super_admin");

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-slate-100 animate-pulse" />
          ))}
        </div>
        <div className="h-64 rounded-xl bg-slate-100 animate-pulse" />
      </div>
    );
  }

  if (!me) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-aic-dark">Admin Dashboard</h1>
        <p className="text-aic-muted text-sm mt-1">
          Manage user accounts, approvals, roles, and access.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 font-bold">✕</button>
        </div>
      )}
      {notice && (
        <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-green-700 text-sm flex items-center justify-between">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-green-400 hover:text-green-600 font-bold">✕</button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={stats.total} accent="text-aic-dark" />
        <StatCard label="Pending Approval" value={stats.pending} accent={stats.pending > 0 ? "text-amber-600" : "text-aic-dark"} />
        <StatCard label="Active" value={stats.active} accent="text-green-700" />
        <StatCard label="Admins" value={stats.admins} accent="text-purple-700" />
      </div>

      {/* Pending approvals */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
          <h2 className="font-semibold text-aic-dark">Pending Approvals</h2>
          {pending.length > 0 && (
            <span className="text-xs font-bold bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">
              {pending.length}
            </span>
          )}
        </div>
        {pending.length === 0 ? (
          <p className="px-5 py-6 text-sm text-aic-muted">No signups waiting for approval.</p>
        ) : (
          <ul className="divide-y divide-slate-50">
            {pending.map((u) => (
              <li key={u.id} className="px-5 py-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-aic-dark">{u.full_name}</p>
                  <p className="text-sm text-aic-muted">{u.email}</p>
                  <p className="text-xs text-slate-400 mt-0.5">Registered {fmtDate(u.created_at)}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() =>
                      withBusy(u.id, async () => {
                        await approveUser(u.id);
                        await loadUsers();
                        setNotice(`Approved ${u.email} — they can sign in now.`);
                      }, "Failed to approve user.")
                    }
                    disabled={busyId === u.id}
                    className="px-4 py-2 bg-aic-green text-white text-sm font-semibold rounded-lg hover:bg-green-800 transition disabled:opacity-50"
                  >
                    {busyId === u.id ? "Working…" : "Approve"}
                  </button>
                  <button
                    onClick={() => {
                      if (!window.confirm(`Reject and delete the signup for ${u.email}? They will be able to register again.`)) return;
                      withBusy(u.id, async () => {
                        await rejectUser(u.id);
                        await loadUsers();
                        setNotice(`Rejected ${u.email}.`);
                      }, "Failed to reject user.");
                    }}
                    disabled={busyId === u.id}
                    className="px-4 py-2 bg-white border border-red-200 text-red-600 text-sm font-semibold rounded-lg hover:bg-red-50 transition disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* All users */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold text-aic-dark">All Users</h2>
          <div className="flex flex-wrap gap-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name or email…"
              className="border border-slate-200 rounded-lg text-sm px-3 py-1.5 w-56 focus:outline-none focus:ring-2 focus:ring-aic-green"
            />
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="border border-slate-200 rounded-lg text-sm px-2 py-1.5 bg-white"
            >
              <option value="">All roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 uppercase tracking-wide border-b border-slate-100">
                <th className="text-left px-5 py-2.5">User</th>
                <th className="text-left px-4 py-2.5">Role</th>
                <th className="text-left px-4 py-2.5">Status</th>
                <th className="text-left px-4 py-2.5">Joined</th>
                <th className="text-right px-5 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => {
                const manageable = canManage(u);
                return (
                  <tr key={u.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                    <td className="px-5 py-3">
                      <p className="font-medium text-aic-dark">
                        {u.full_name}
                        {u.id === me.id && (
                          <span className="ml-2 text-[10px] font-bold uppercase text-slate-400">you</span>
                        )}
                      </p>
                      <p className="text-xs text-aic-muted">{u.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      {manageable ? (
                        <select
                          value={u.role}
                          disabled={busyId === u.id}
                          onChange={(e) => {
                            const role = e.target.value;
                            withBusy(u.id, async () => {
                              await setUserRole(u.id, role);
                              await loadUsers();
                              setNotice(`Changed ${u.email} to ${ROLE_LABELS[role] ?? role}.`);
                            }, "Failed to change role.");
                          }}
                          className={`text-xs font-semibold rounded-full px-2 py-1 border-0 cursor-pointer ${ROLE_BADGE[u.role] ?? ROLE_BADGE.viewer}`}
                        >
                          {ROLES.filter((r) => r !== "super_admin" || me.role === "super_admin").map((r) => (
                            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`text-xs font-semibold rounded-full px-2.5 py-1 ${ROLE_BADGE[u.role] ?? ROLE_BADGE.viewer}`}>
                          {ROLE_LABELS[u.role] ?? u.role}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {!u.is_verified ? (
                          <span className="text-[11px] font-semibold bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">Pending</span>
                        ) : u.is_active ? (
                          <span className="text-[11px] font-semibold bg-green-100 text-green-700 rounded-full px-2 py-0.5">Active</span>
                        ) : (
                          <span className="text-[11px] font-semibold bg-red-100 text-red-700 rounded-full px-2 py-0.5">Deactivated</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{fmtDate(u.created_at)}</td>
                    <td className="px-5 py-3 text-right">
                      {manageable && u.is_verified && (
                        <button
                          onClick={() => {
                            if (u.is_active && !window.confirm(`Deactivate ${u.email}? They will no longer be able to sign in.`)) return;
                            withBusy(u.id, async () => {
                              await setUserActive(u.id, !u.is_active);
                              await loadUsers();
                              setNotice(`${u.is_active ? "Deactivated" : "Reactivated"} ${u.email}.`);
                            }, "Failed to update account status.");
                          }}
                          disabled={busyId === u.id}
                          className={`text-xs font-semibold rounded-lg px-3 py-1.5 border transition disabled:opacity-50 ${
                            u.is_active
                              ? "border-red-200 text-red-600 hover:bg-red-50"
                              : "border-green-200 text-green-700 hover:bg-green-50"
                          }`}
                        >
                          {busyId === u.id ? "Working…" : u.is_active ? "Deactivate" : "Reactivate"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-sm text-aic-muted">
                    No users match the current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
