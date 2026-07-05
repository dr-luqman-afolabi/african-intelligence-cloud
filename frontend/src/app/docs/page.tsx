"use client";
import Link from "next/link";

const ENDPOINTS = [
  {
    group: "Authentication",
    items: [
      {
        method: "POST",
        path: "/auth/register",
        desc: "Register a new user account",
        body: '{ "email": "...", "password": "...", "full_name": "..." }',
        response: "UserProfile",
      },
      {
        method: "POST",
        path: "/auth/login",
        desc: "Obtain a JWT access token",
        body: '{ "email": "...", "password": "..." }',
        response: '{ access_token, token_type }',
      },
      {
        method: "GET",
        path: "/auth/profile",
        desc: "Return the current authenticated user's profile",
        auth: true,
        response: "UserProfile",
      },
    ],
  },
  {
    group: "Countries & Indicators",
    items: [
      { method: "GET", path: "/countries", desc: "List all 54 African countries" },
      { method: "GET", path: "/indicators", desc: "List all tracked economic indicators" },
      { method: "GET", path: "/macro-data", desc: "Query time-series data by country + indicator" },
    ],
  },
  {
    group: "Datasets",
    items: [
      { method: "GET", path: "/datasets", desc: "Paginated list of uploaded datasets" },
      { method: "POST", path: "/datasets/upload", desc: "Upload a CSV/Excel/Parquet dataset" },
      { method: "GET", path: "/datasets/{id}", desc: "Dataset detail with column profiles" },
      { method: "POST", path: "/datasets/{id}/profile", desc: "Trigger column profiling job" },
      { method: "DELETE", path: "/datasets/{id}", desc: "Delete a dataset" },
    ],
  },
  {
    group: "Data Connectors",
    items: [
      { method: "GET", path: "/connectors", desc: "List all registered data source connectors" },
      { method: "GET", path: "/connectors/{id}/health", desc: "Live health check for a connector" },
      { method: "POST", path: "/connectors/{id}/sync", desc: "Trigger a manual data sync" },
      { method: "GET", path: "/connectors/{id}/sync/history", desc: "Sync job history" },
    ],
  },
  {
    group: "Health Monitoring",
    items: [
      { method: "GET", path: "/health/sources", desc: "Aggregate health for all data sources" },
      { method: "GET", path: "/health/sources/{id}", desc: "Health detail for a single source" },
    ],
  },
  {
    group: "AI Research (RAG)",
    items: [
      {
        method: "POST",
        path: "/rag/query",
        desc: "Ask a natural language question; returns an AI answer with source citations",
        body: '{ "query": "...", "history": [] }',
        response: '{ answer, sources, query_id }',
      },
    ],
  },
  {
    group: "Semantic Search",
    items: [
      {
        method: "GET",
        path: "/search/semantic",
        desc: "Natural language search over all indicators and datasets",
        query: "?q=poverty+headcount&limit=10",
        response: "SearchResult[]",
      },
    ],
  },
  {
    group: "SDG Analytics",
    items: [
      {
        method: "GET",
        path: "/sdg/goals",
        desc: "List all 17 SDG goals with matched indicators from the AIC database",
      },
      {
        method: "GET",
        path: "/sdg/data",
        desc: "Time-series data for a specific SDG goal, optionally filtered by country",
        query: "?goal=1&country=NGA",
      },
    ],
  },
  {
    group: "Surveys & Schedules",
    items: [
      { method: "GET", path: "/surveys", desc: "List household survey datasets" },
      { method: "GET", path: "/schedules", desc: "List connector sync schedules" },
    ],
  },
];

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-green-100 text-green-700",
  POST: "bg-blue-100 text-blue-700",
  DELETE: "bg-red-100 text-red-700",
  PUT: "bg-yellow-100 text-yellow-700",
};

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">API Reference</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Base URL:{" "}
              <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono">
                {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1
              </code>
            </p>
          </div>
          <Link
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded-xl bg-aic-dark text-white hover:bg-slate-700 transition font-medium"
          >
            Open Interactive Docs ↗
          </Link>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-amber-800 text-sm">
          All protected endpoints require{" "}
          <code className="font-mono bg-amber-100 px-1 rounded text-xs">
            Authorization: Bearer &lt;token&gt;
          </code>{" "}
          in the request header. Obtain a token from <strong>POST /auth/login</strong>.
        </div>

        {ENDPOINTS.map((group) => (
          <div key={group.group} className="bg-white rounded-xl border border-slate-200 shadow-sm">
            <div className="px-4 py-3 border-b border-slate-100">
              <h2 className="font-bold text-slate-800 text-sm">{group.group}</h2>
            </div>
            <div className="divide-y divide-slate-50">
              {group.items.map((ep, i) => (
                <div key={i} className="px-4 py-3 space-y-1.5">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${METHOD_COLORS[ep.method] ?? "bg-slate-100 text-slate-700"}`}
                    >
                      {ep.method}
                    </span>
                    <code className="font-mono text-xs text-slate-700">
                      {ep.path}
                      {(ep as { query?: string }).query ?? ""}
                    </code>
                    {(ep as { auth?: boolean }).auth && (
                      <span className="text-xs text-slate-400">🔒 Auth required</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">{ep.desc}</p>
                  {(ep as { body?: string }).body && (
                    <pre className="text-[11px] bg-slate-50 rounded-lg px-3 py-2 font-mono text-slate-600 overflow-x-auto">
                      {(ep as { body?: string }).body}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
