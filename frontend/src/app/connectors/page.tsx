"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchConnectors,
  fetchConnectorHealth,
  fetchSyncHistory,
  triggerConnectorSync,
  type ConnectorHealth,
  type SyncJob,
} from "@/lib/api";

// Registry shape returned by GET /connectors (merges registry.py + connector_registered flag)
interface ConnectorListItem {
  source_id: string;
  source_name: string;
  source_type: string;      // registry field used as description
  access_method: string;
  license_category: string;
  update_frequency: string;
  connector_status: string;
  connector_registered: boolean;
  requires_approval: boolean;
  redistribution_allowed: boolean;
  citation_required: boolean;
  data_owner: string;
}

const LICENSE_BADGE: Record<string, string> = {
  A: "bg-emerald-100 text-emerald-800",
  B: "bg-blue-100 text-blue-800",
  C: "bg-amber-100 text-amber-800",
  D: "bg-slate-100 text-slate-600",
};

const STATUS_BADGE: Record<string, string> = {
  live: "bg-emerald-100 text-emerald-700",
  planned: "bg-amber-100 text-amber-700",
  deprecated: "bg-red-100 text-red-700",
};

const FREQ_LABEL: Record<string, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  annual: "Annual",
  quarterly: "Quarterly",
  irregular: "Irregular",
  on_demand: "On demand",
  per_round: "Per round",
};

function HealthDot({ healthy }: { healthy: boolean | null }) {
  if (healthy === null)
    return <span className="inline-block w-2.5 h-2.5 rounded-full bg-slate-300" title="Not checked" />;
  return healthy ? (
    <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" title="Healthy" />
  ) : (
    <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-400" title="Unhealthy" />
  );
}

function SyncStatusPill({ status }: { status: string }) {
  const cls: Record<string, string> = {
    success: "bg-emerald-100 text-emerald-700",
    failed: "bg-red-100 text-red-700",
    running: "bg-blue-100 text-blue-700",
    partial: "bg-amber-100 text-amber-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls[status] ?? "bg-slate-100 text-slate-600"}`}>
      {status}
    </span>
  );
}

interface ConnectorRowProps {
  connector: ConnectorListItem;
}

function ConnectorRow({ connector }: ConnectorRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [health, setHealth] = useState<ConnectorHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthErr, setHealthErr] = useState<string | null>(null);
  const [syncJobs, setSyncJobs] = useState<SyncJob[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [syncErr, setSyncErr] = useState<string | null>(null);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  const checkHealth = useCallback(async () => {
    setHealthLoading(true);
    setHealthErr(null);
    try {
      const h = await fetchConnectorHealth(connector.source_id);
      setHealth(h);
    } catch {
      setHealthErr("Health check failed");
    } finally {
      setHealthLoading(false);
    }
  }, [connector.source_id]);

  const loadHistory = useCallback(async () => {
    if (historyLoaded) return;
    try {
      const jobs = await fetchSyncHistory(connector.source_id);
      setSyncJobs(jobs);
      setHistoryLoaded(true);
    } catch {
      // non-critical
    }
  }, [connector.source_id, historyLoaded]);

  const handleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    if (next) loadHistory();
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg(null);
    setSyncErr(null);
    try {
      const res = await triggerConnectorSync(connector.source_id);
      setSyncMsg(res.message);
      setHistoryLoaded(false);
      setTimeout(() => {
        loadHistory();
        setHistoryLoaded(false);
      }, 2000);
    } catch {
      setSyncErr("Sync request failed");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="border border-slate-100 rounded-xl bg-white shadow-sm overflow-hidden">
      {/* Header row */}
      <div className="flex items-center gap-3 px-5 py-4">
        <HealthDot healthy={health?.healthy ?? null} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-aic-dark text-sm">{connector.source_name}</span>
            <code className="text-xs text-slate-400 font-mono">{connector.source_id}</code>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 truncate">{connector.source_type}</p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${LICENSE_BADGE[connector.license_category] ?? "bg-slate-100 text-slate-600"}`}>
            Lic {connector.license_category}
          </span>
          <span className="text-xs text-slate-400">
            {FREQ_LABEL[connector.update_frequency] ?? connector.update_frequency}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[connector.connector_status] ?? "bg-slate-100 text-slate-600"}`}>
            {connector.connector_status}
          </span>
          <button
            onClick={checkHealth}
            disabled={healthLoading}
            className="text-xs px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 disabled:opacity-50 transition"
          >
            {healthLoading ? "…" : "Health"}
          </button>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="text-xs px-2.5 py-1 rounded-lg bg-aic-green text-white hover:bg-green-700 disabled:opacity-50 transition font-medium"
          >
            {syncing ? "Syncing…" : "Sync"}
          </button>
          <button
            onClick={handleExpand}
            className="text-xs px-2 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500 transition"
          >
            {expanded ? "▲" : "▼"}
          </button>
        </div>
      </div>

      {/* Inline health result */}
      {(health || healthErr) && (
        <div className={`px-5 py-2 text-xs border-t border-slate-50 ${health?.healthy === false ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
          {healthErr ? (
            healthErr
          ) : health ? (
            <>
              {health.healthy ? "✓ Healthy" : "✗ Unhealthy"} —{" "}
              {health.latency_ms !== null ? `${health.latency_ms} ms` : ""}
              {health.message ? ` · ${health.message}` : ""}
              {" · checked "}
              {new Date(health.checked_at).toLocaleTimeString()}
            </>
          ) : null}
        </div>
      )}

      {/* Sync feedback */}
      {(syncMsg || syncErr) && (
        <div className={`px-5 py-2 text-xs border-t border-slate-50 ${syncErr ? "bg-red-50 text-red-700" : "bg-blue-50 text-blue-700"}`}>
          {syncErr ?? syncMsg}
        </div>
      )}

      {/* Expanded: sync history */}
      {expanded && (
        <div className="border-t border-slate-100 px-5 py-4 bg-slate-50">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Sync History
          </h4>
          {syncJobs.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No sync jobs yet.</p>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400">
                  <th className="pb-1 font-medium pr-4">Status</th>
                  <th className="pb-1 font-medium pr-4">Fetched</th>
                  <th className="pb-1 font-medium pr-4">Written</th>
                  <th className="pb-1 font-medium pr-4">Started</th>
                  <th className="pb-1 font-medium">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {syncJobs.map((job) => {
                  const started = job.started_at ? new Date(job.started_at) : null;
                  const finished = job.finished_at ? new Date(job.finished_at) : null;
                  const durSec =
                    started && finished
                      ? ((finished.getTime() - started.getTime()) / 1000).toFixed(1)
                      : null;
                  return (
                    <tr key={job.id} className="text-slate-600">
                      <td className="py-1.5 pr-4">
                        <SyncStatusPill status={job.status} />
                      </td>
                      <td className="py-1.5 pr-4">{job.records_fetched ?? "—"}</td>
                      <td className="py-1.5 pr-4">{job.records_written ?? "—"}</td>
                      <td className="py-1.5 pr-4">
                        {started ? started.toLocaleString() : "—"}
                      </td>
                      <td className="py-1.5">
                        {durSec !== null ? `${durSec}s` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          {syncJobs.some((j) => j.error_message) && (
            <div className="mt-3 space-y-1">
              {syncJobs
                .filter((j) => j.error_message)
                .slice(0, 3)
                .map((j) => (
                  <p key={j.id} className="text-xs text-red-600 bg-red-50 rounded px-2 py-1">
                    {j.error_message}
                  </p>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const TIER_PREFIXES: Record<string, string[]> = {
  "Tier 1 — World Bank & UN": [
    "world_bank", "un_comtrade", "fao_faostat", "who_gho", "undp_hdr", "ilo_ilostat",
    "wb_poverty", "imf_weo", "unhcr", "unicef_mics",
  ],
  "Tier 2 — Financial & Regional": [
    "africanbond", "mfin_cbn", "dhs_program", "nbs_nigeria", "afdb_statistics",
    "transparency_intl", "doing_business", "hies_lsms", "oecd_devstats",
    "kobotoolbox_client",
  ],
  "Tier 3 — Governance, Climate & Geospatial": [
    "ophi_mpi", "owid", "polity5", "pts", "vdem", "afrobarometer_public",
    "acled", "aiddata", "global_carbon_project", "climate_watch", "nasa_power",
    "climate_chirps", "era5", "osm",
  ],
};

function groupByTier(connectors: ConnectorListItem[]) {
  const idToConnector = Object.fromEntries(connectors.map((c) => [c.source_id, c]));
  const result: Array<{ tier: string; items: ConnectorListItem[] }> = [];
  const seen = new Set<string>();

  for (const [tier, ids] of Object.entries(TIER_PREFIXES)) {
    const items = ids
      .map((id) => idToConnector[id])
      .filter((c): c is ConnectorListItem => !!c);
    items.forEach((c) => seen.add(c.source_id));
    if (items.length) result.push({ tier, items });
  }

  // Anything not in a known tier
  const rest = connectors.filter((c) => !seen.has(c.source_id));
  if (rest.length) result.push({ tier: "Other", items: rest });

  return result;
}

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchConnectors()
      .then(setConnectors)
      .catch(() => setError("Failed to load connectors. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = connectors.filter((c) => {
    const matchSearch =
      !search ||
      c.source_name.toLowerCase().includes(search.toLowerCase()) ||
      c.source_id.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || c.connector_status === statusFilter;
    return matchSearch && matchStatus;
  });

  const grouped = groupByTier(filtered);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-aic-dark mb-1">Data Connectors</h1>
        <p className="text-aic-muted text-sm">
          {connectors.length} sources registered — click Health to probe, Sync to pull data
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search connectors…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm w-64 focus:outline-none focus:ring-2 focus:ring-aic-green"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-aic-green"
        >
          <option value="all">All statuses</option>
          <option value="live">Live</option>
          <option value="planned">Planned</option>
          <option value="deprecated">Deprecated</option>
        </select>
        <div className="flex items-center gap-4 text-xs text-slate-500 ml-auto">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            Healthy
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
            Unhealthy
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-slate-300 inline-block" />
            Not checked
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-4 border-aic-green border-t-transparent rounded-full" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-aic-muted py-20">
          No connectors match your filters.
        </div>
      ) : (
        <div className="space-y-10">
          {grouped.map(({ tier, items }) => (
            <section key={tier}>
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-3">
                {tier}
                <span className="ml-2 font-normal normal-case tracking-normal text-slate-400">
                  ({items.length})
                </span>
              </h2>
              <div className="space-y-2">
                {items.map((c) => (
                  <ConnectorRow key={c.source_id} connector={c} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
