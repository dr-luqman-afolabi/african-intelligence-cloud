"use client";

import { useState } from "react";
import Link from "next/link";
import { generateLiteratureReview, LiteratureReviewResponse } from "@/lib/api";
import { LiteratureMatrixTable } from "@/components/research/LiteratureMatrixTable";
import { TheoryPanel } from "@/components/research/TheoryPanel";
import { MethodPanel } from "@/components/research/MethodPanel";
import { ExportButton } from "@/components/research/ExportButton";

export default function LiteratureReviewPage() {
  const [topic, setTopic] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LiteratureReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await generateLiteratureReview({
        topic: topic.trim(),
        year_from: yearFrom ? parseInt(yearFrom) : undefined,
        year_to: yearTo ? parseInt(yearTo) : undefined,
        max_results: 30,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate review");
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
        <h1 className="text-base font-semibold text-slate-800">Literature Review</h1>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Input form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <p className="text-sm text-slate-500">
            Enter a research topic to generate a structured literature matrix, identify gaps, and get theory and method recommendations.
          </p>
          <form onSubmit={handleGenerate} className="space-y-3">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Financial inclusion and poverty reduction in Sub-Saharan Africa"
              className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
            />
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-sm">
                <label className="text-slate-500 whitespace-nowrap">Year range:</label>
                <input
                  type="number"
                  placeholder="From"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                  min={1900}
                  max={2100}
                  className="w-24 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none"
                />
                <span className="text-slate-400">–</span>
                <input
                  type="number"
                  placeholder="To"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                  min={1900}
                  max={2100}
                  className="w-24 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !topic.trim()}
                className="px-5 py-2 bg-slate-900 text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
              >
                {loading ? "Generating…" : "Generate Review"}
              </button>
            </div>
          </form>
        </div>

        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-16 text-sm text-slate-400">
            Searching databases and generating review…
          </div>
        )}

        {!loading && result && (
          <div className="space-y-6">
            {/* Summary bar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <h2 className="text-base font-semibold text-slate-900">{result.topic}</h2>
                <p className="text-sm text-slate-500">{result.total_papers} papers analysed</p>
              </div>
              <ExportButton papers={result.matrix} />
            </div>

            {/* Research gaps */}
            {result.research_gaps.length > 0 && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 space-y-2">
                <h3 className="text-sm font-semibold text-amber-800">Research Gaps Identified</h3>
                <ul className="space-y-1.5">
                  {result.research_gaps.map((gap, i) => (
                    <li key={i} className="text-sm text-amber-700 flex gap-2">
                      <span className="shrink-0 font-bold">·</span>
                      <span>{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Literature matrix */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">Literature Matrix</h3>
              <LiteratureMatrixTable rows={result.matrix} />
            </div>

            {/* Theory and method panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TheoryPanel theories={result.recommended_theories} />
              <MethodPanel methods={result.recommended_methods} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
