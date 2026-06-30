"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendResearchVariables, VariableRecommendationResponse } from "@/lib/api";
import { DatasetPanel } from "@/components/research/DatasetPanel";

export default function DataRecommendationPage() {
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VariableRecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await recommendResearchVariables({
        topic: topic.trim(),
        context: context.trim() || undefined,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get recommendations");
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
        <h1 className="text-base font-semibold text-slate-800">Data & Variable Recommendations</h1>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <p className="text-sm text-slate-500">
            Describe your research topic to get recommended variables, African datasets, a conceptual framework, and testable hypotheses.
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Research topic (e.g. Determinants of FDI in Sub-Saharan Africa)"
              className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
            />
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Optional context — e.g. panel data, macroeconomic study, 2000–2023..."
              rows={2}
              className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none resize-none focus:ring-2 focus:ring-green-600"
            />
            <button
              type="submit"
              disabled={loading || !topic.trim()}
              className="px-5 py-2.5 bg-slate-900 text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
            >
              {loading ? "Generating…" : "Get Recommendations"}
            </button>
          </form>
        </div>

        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-16 text-sm text-slate-400">Generating recommendations…</div>
        )}

        {!loading && result && (
          <div className="space-y-6">
            <h2 className="text-base font-semibold text-slate-900">{result.topic}</h2>

            {/* Variables */}
            {result.recommended_variables.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Recommended Variables</h3>
                <div className="space-y-2">
                  {result.recommended_variables.map((v) => (
                    <div key={v.variable} className="rounded-xl bg-slate-50 border border-slate-100 p-4 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-slate-900">{v.variable}</span>
                        <span className="text-xs bg-green-50 text-green-700 rounded-full px-2 py-0.5">
                          {Math.round(v.relevance_score * 100)}% match
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {v.recommended_sources.map((src) => (
                          <span key={src} className="text-xs bg-white border border-slate-200 text-slate-600 rounded-full px-2 py-0.5">
                            {src}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Datasets */}
            <DatasetPanel datasets={result.african_datasets} />

            {/* Conceptual framework */}
            {result.conceptual_framework && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-700">Conceptual Framework</h3>
                <p className="text-sm font-medium text-slate-900">{result.conceptual_framework.title}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Theoretical Foundations</p>
                    <ul className="space-y-0.5">
                      {result.conceptual_framework.theoretical_foundation.map((t) => (
                        <li key={t} className="text-slate-600">• {t}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Independent Variables</p>
                    <ul className="space-y-0.5">
                      {result.conceptual_framework.independent_variables.map((v) => (
                        <li key={v} className="text-slate-600">• {v}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Dependent Variable</p>
                    <p className="text-slate-600">{result.conceptual_framework.dependent_variable}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Moderating Factors</p>
                    <ul className="space-y-0.5">
                      {result.conceptual_framework.moderating_factors.map((f) => (
                        <li key={f} className="text-slate-600">• {f}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                {result.conceptual_framework.proposed_relationships.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Proposed Relationships</p>
                    <ul className="space-y-0.5">
                      {result.conceptual_framework.proposed_relationships.map((r) => (
                        <li key={r} className="text-sm text-slate-600">• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Hypotheses */}
            {result.hypotheses.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Proposed Hypotheses</h3>
                <ol className="space-y-2 list-decimal list-inside">
                  {result.hypotheses.map((h, i) => (
                    <li key={i} className="text-sm text-slate-600 leading-relaxed">{h}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
