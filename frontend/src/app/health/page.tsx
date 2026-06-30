"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { fetchSourcesHealth, HealthSourcesResponse, SourceHealthEntry } from "@/lib/api";

type Filter = "all" | "healthy" | "unhealthy";

function StatusDot({ healthy }: { healthy: boolean | null }) {
  if (healthy === null)
    return <span className="inline-block w-2.5 h-2.5 rounded-full bg-slate-400" title="unknown" />;
  return (
    <span
      className={clsx(
        "inline-block w-2.5 h-2.5 rounded-full",
        healthy ? "bg-green-500" : "bg-red-500"
      )}
      title={healthy ? "healthy" : "unhealthy"}
    />
  );
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col gap-1">
      <span className="text-xs text-slate-500 uppercase tracking-wide">{label}</span>
      <span className={clsx("text-3xl font-bold", accent ?? "text-slate-800")}>{value}</span>
    </div>
  );
}

function fmtDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtLatency(ms: number | null) {
  if (ms === null) return "—";
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

const LICENSE_COLORS: Record<string, string> = {
  open: "bg-green-100 text-green-800",
  restricted: "bg-yellow-100 text-yellow-800",
  commercial: "bg-blue-100 text-blue-800",
  closed: "bg-red-100 text-red-800",
};

function LicenseBadge({ cat }: { cat: string | null }) {
  if (!cat) return null;
  const cls = LICENSE_COLORS[cat.toLowerCase()] ?? "bg-slate-100 text-slate-700";
  return (
    <span className={clsx("px-1.5 py-0.5 rounded text-xs font-medium uppercase", cls)}>{cat}</span>
  );
}

export default function HealthPage() {
  const [data, setData] = useState<HealthSourcesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const resp = await fetchSourcesHealth({ limit: 200 });
      setData(resp);
      setLastRefreshed(new Date());
      setError(null);
    } catch {
      setError("Failed to load health data — is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(load, 30_000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, load]);

  const filtered: SourceHealthEntry[] = (data?.sources ?? []).filter((s) => {
    if (filter === "healthy") return s.healthy === true;
    if (filter === "unhealthy") return s.healthy !== true;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Source Health Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time status for all registered data connectors
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-xs text-slate-400">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={() => setAutoRefresh((v) => !v)}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-sm font-medium border transition",
              autoRefresh
                ? "bg-green-600 text-white border-green-600"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            )}
          >
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </button>
          <button
            onClick={load}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-white border border-slate-300 hover:bg-slate-50 disabled:opacity-50 transition"
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <SummaryCard label="Total Sources" value={data.total_sources} />
          <SummaryCard
            label="Healthy"
            value={data.summary.healthy}
            accent="text-green-600"
          />
          <SummaryCard
            label="Unhealthy"
            value={data.summary.unhealthy}
            accent="text-red-600"
          />
          <SummaryCard
            label="Coverage"
            value={
              data.total_sources > 0
                ? `${Math.round((data.summary.healthy / data.total_sources) * 100)}%`
                : "—"
            }
            accent="text-aic-green"
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-2">
        {(["all", "healthy", "unhealthy"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              "px-4 py-1.5 rounded-full text-sm font-medium transition capitalize",
              filter === f
                ? "bg-aic-dark text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {f}
            {data && (
              <span className="ml-1.5 text-xs">
                (
                {f === "all"
                  ? data.sources.length
                  : f === "healthy"
                  ? data.summary.healthy
                  : data.summary.unhealthy}
                )
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      {loading && !data ? (
        <div className="text-center py-20 text-slate-400">Loading health data…</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Source</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">License</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Frequency</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Latency</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Last Synced</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Records</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Message</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-400">
                    No sources match the current filter.
                  </td>
                </tr>
              )}
              {filtered.map((s) => (
                <tr
                  key={s.source_id}
                  className={clsx(
                    "border-b border-slate-100 hover:bg-slate-50 transition",
                    s.healthy === false && "bg-red-50/30"
                  )}
                >
                  <td className="px-4 py-3">
                    <StatusDot healthy={s.healthy} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">
                      {s.source_name ?? s.source_id}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">{s.source_id}</div>
                  </td>
                  <td className="px-4 py-3">
                    <LicenseBadge cat={s.license_category} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {s.update_frequency ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700">
                    {fmtLatency(s.latency_ms)}
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                    {fmtDate(s.last_synced_at)}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700">
                    {s.records_synced ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                    {s.message ?? ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
