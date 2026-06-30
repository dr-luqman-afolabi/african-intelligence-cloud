"use client";
import { useState } from "react";
import { semanticSearch, SearchResult } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await semanticSearch(query.trim());
      setResults(res);
      setSearched(true);
    } catch {
      setError("Search failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-800">Semantic Dataset Search</h1>
          <p className="text-sm text-slate-500">
            Natural language search over all African economic indicators and datasets
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. unemployment rates in Sub-Saharan Africa…"
            className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-aic-green shadow-sm"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 bg-aic-dark text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </form>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {searched && results.length === 0 && !loading && (
          <div className="text-center py-16 text-slate-400 text-sm">
            No datasets found for &ldquo;{query}&rdquo;
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
              {results.length} result{results.length !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
            </p>
            {results.map((r, i) => (
              <div
                key={r.dataset_id}
                className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400 tabular-nums w-5">
                      {i + 1}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-800">{r.title}</h3>
                  </div>
                  <span className="shrink-0 text-xs bg-aic-green/10 text-aic-green font-semibold px-2 py-0.5 rounded-full">
                    {(r.score * 100).toFixed(0)}% match
                  </span>
                </div>
                <p className="text-xs text-slate-500 pl-7">{r.description}</p>
                <div className="pl-7 flex flex-wrap items-center gap-2">
                  {r.tags.map((t) => (
                    <span
                      key={t}
                      className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5"
                    >
                      {t}
                    </span>
                  ))}
                  <span className="text-xs text-slate-400 ml-auto">
                    {r.record_count.toLocaleString()} records
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {!searched && (
          <div className="text-center py-16 space-y-3">
            <div className="text-4xl">🔍</div>
            <p className="text-slate-400 text-sm">
              Try: &ldquo;poverty headcount ratio&rdquo;, &ldquo;trade balance Nigeria&rdquo;,
              &ldquo;maternal mortality East Africa&rdquo;
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
