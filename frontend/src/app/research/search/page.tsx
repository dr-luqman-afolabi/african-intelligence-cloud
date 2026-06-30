"use client";

import { useState } from "react";
import Link from "next/link";
import { searchResearchPapers, PaperSearchResponse } from "@/lib/api";
import { SearchBar } from "@/components/research/SearchBar";
import { PaperResultCard } from "@/components/research/PaperResultCard";

export default function ResearchSearchPage() {
  const [results, setResults] = useState<PaperSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(params: {
    q: string;
    source: string;
    year_from?: number;
    year_to?: number;
    max_results: number;
  }) {
    setLoading(true);
    setError(null);
    try {
      const res = await searchResearchPapers(params);
      setResults(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Search failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-6 py-4 flex items-center gap-3">
        <Link href="/research" className="text-slate-400 hover:text-slate-600 transition text-sm">
          ← Research
        </Link>
        <span className="text-slate-300">/</span>
        <h1 className="text-base font-semibold text-slate-800">Search Papers</h1>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-16 text-sm text-slate-400">Searching…</div>
        )}

        {!loading && results && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">
                <span className="font-semibold text-slate-900">{results.total.toLocaleString()}</span> results
                {" "}via <span className="font-medium">{results.source}</span>
                {" "}for <span className="italic">&ldquo;{results.query}&rdquo;</span>
              </p>
            </div>
            {results.results.length === 0 ? (
              <div className="rounded-2xl bg-white border border-slate-200 p-8 text-center text-sm text-slate-400">
                No papers found. Try a different query or source.
              </div>
            ) : (
              <div className="space-y-3">
                {results.results.map((paper, i) => (
                  <PaperResultCard key={paper.external_id || i} paper={paper} />
                ))}
              </div>
            )}
          </div>
        )}

        {!loading && !results && !error && (
          <div className="text-center py-16 text-sm text-slate-400">
            Enter a query above to search for research papers.
          </div>
        )}
      </div>
    </div>
  );
}
