"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCurrentUser, fetchPendingUsers, approveUser, AuthUser } from "@/lib/api";

export default function AdminUsersPage() {
  const router = useRouter();
  const [me, setMe] = useState<AuthUser | null>(null);
  const [pending, setPending] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("aic_token");
    if (!token) {
      router.replace("/login");
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
        const list = await fetchPendingUsers();
        setPending(list);
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function handleApprove(id: string) {
    setApprovingId(id);
    try {
      await approveUser(id);
      setPending((prev) => prev.filter((u) => u.id !== id));
    } catch {
      setError("Failed to approve user. Please try again.");
    } finally {
      setApprovingId(null);
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <p className="text-aic-muted">Loading...</p>
      </div>
    );
  }

  if (!me) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-aic-dark mb-2">Pending Signups</h1>
      <p className="text-aic-muted mb-6">
        Review and approve new user registrations before they can sign in.
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm mb-6">
          {error}
        </div>
      )}

      {pending.length === 0 ? (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <p className="text-aic-muted">No pending signups right now.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {pending.map((user) => (
            <div
              key={user.id}
              className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 flex items-center justify-between"
            >
              <div>
                <p className="font-semibold text-aic-dark">{user.full_name}</p>
                <p className="text-sm text-aic-muted">{user.email}</p>
                <p className="text-xs text-aic-muted mt-1">Role: {user.role}</p>
              </div>
              <button
                onClick={() => handleApprove(user.id)}
                disabled={approvingId === user.id}
                className="px-6 py-3 bg-aic-green text-white font-semibold rounded-lg hover:bg-green-800 transition disabled:opacity-50"
              >
                {approvingId === user.id ? "Approving..." : "Approve"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
