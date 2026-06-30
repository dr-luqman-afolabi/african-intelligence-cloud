"use client";

import { useState } from "react";
import Link from "next/link";
import { recommendResearchMethods, recommendResearchTheories, MethodRecommendation, TheoryRecommendation } from "@/lib/api";
import { MethodPanel } from "@/components/research/MethodPanel";
import { TheoryPanel } from "@/components/research/TheoryPanel";

export default function MethodAdvisorPage() {
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [methods, setMethods] = useState<MethodRecommendation[] | null>(null);
  const [theories, setTheories] = useState<TheoryRecommendation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    setMethods(null);
    setTheories(null);
    try {
      const req = { topic: topic.trim(), context: context.trim() || undefined };
      const [mRes, tRes] = await Promise.all([
        recommendResearchMethods(req),
        recommendResearchTheories(req),
      ]);
      setMethods(mRes.recommended_methods);
      setTheories(tRes.recommended_theories);
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
        <h1 className="text-base font-semibold text-slate-800">Method Advisor</h1>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <p className="text-sm text-slate-500">
            Describe your research topic and optional context to receive AI-matched methodology and theory recommendations.
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Research topic (e.g. Impact of mobile banking on rural poverty in Kenya)"
              className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
            />
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Additional context (optional) — e.g. quantitative study, cross-sectional, secondary data..."
              rows={3}
              className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-600 resize-none"
            />
            <button
              type="submit"
              disabled={loading || !topic.trim()}
              className="px-5 py-2.5 bg-slate-900 text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
            >
              {loading ? "Analysing…" : "Get Recommendations"}
            </button>
          </form>
        </div>

        {error && (
          <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-16 text-sm text-slate-400">Analysing topic…</div>
        )}

        {!loading && (methods || theories) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {methods && <MethodPanel methods={methods} />}
            {theories && <TheoryPanel theories={theories} />}
          </div>
        )}
      </div>
    </div>
  );
}
