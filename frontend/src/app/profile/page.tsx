"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCurrentUser, AuthUser } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("aic_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser()
      .then((data) => setUser(data))
      .catch(() => setError("Could not load your profile. Please sign in again."))
      .finally(() => setLoading(false));
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("aic_token");
    router.push("/login");
  }

  if (loading) {
    return (
      <main className="flex justify-center px-4 py-24">
        <Spinner />
      </main>
    );
  }

  if (error || !user) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-16 text-center">
        <p className="text-aic-muted mb-4">
          {error ?? "You need to sign in to view your profile."}
        </p>
        <a href="/login" className="btn-primary px-6 py-3">
          Go to Login
        </a>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-16 rounded-full bg-aic-green text-white flex items-center justify-center text-2xl font-bold">
          {user.full_name?.charAt(0)?.toUpperCase() ?? "?"}
        </div>
        <div>
          <h1 className="text-3xl font-bold text-aic-dark">{user.full_name}</h1>
          <p className="text-aic-muted">{user.email}</p>
        </div>
      </div>

      <div className="card p-6 space-y-4">
        <div className="flex justify-between border-b border-slate-100 pb-3">
          <span className="text-aic-muted text-sm">Full name</span>
          <span className="font-semibold text-aic-dark">{user.full_name}</span>
        </div>
        <div className="flex justify-between border-b border-slate-100 pb-3">
          <span className="text-aic-muted text-sm">Email</span>
          <span className="font-semibold text-aic-dark">{user.email}</span>
        </div>
        <div className="flex justify-between border-b border-slate-100 pb-3">
          <span className="text-aic-muted text-sm">Role</span>
          <span className="font-semibold text-aic-dark capitalize">{user.role}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-aic-muted text-sm">Account status</span>
          <span
            className={`font-semibold ${
              user.is_active ? "text-aic-green" : "text-aic-red"
            }`}
          >
            {user.is_active ? "Active" : "Inactive"}
          </span>
        </div>
      </div>

      {(user.role === "super_admin" || user.role === "org_admin") && (
        <a
          href="/admin/users"
          className="mt-6 inline-block text-sm font-semibold text-aic-green hover:underline"
        >
          Manage pending signups →
        </a>
      )}

      <button onClick={handleLogout} className="btn-secondary mt-8 px-6 py-3">
        Log out
      </button>
    </main>
  );
}
