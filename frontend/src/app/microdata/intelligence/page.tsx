"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AIPolicyBriefPanel from "@/components/microdata/AIPolicyBriefPanel";
import {
  fetchMicrodataDatasets,
  planIntelligence,
  cleanIntelligence,
  runIntelligenceAnalysis,
  type MicrodataDataset,
  type IntelligencePlan,
  type IntelligenceCleanResponse,
  type AnalysisResultResponse,
} from "@/lib/api";

const EXAMPLES = [
  "What is the poverty rate by district at a line of 2.15?",
  "Show me poverty hotspots across regions on a map",
  "Which areas have the highest crop yields?",
  "How diversified are household incomes, drop rows missing income?",
];

export default function AICIntelligencePage() {
  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [question, setQuestion] = useState("");
  const [plan, setPlan] = useState<IntelligencePlan | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [autoClean, setAutoClean] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cleanInfo, setCleanInfo] = useState<IntelligenceCleanResponse | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);

  useEffect(() => {
    fetchMicrodataDatasets(0, 100)
      .then((res) => {
        setDatasets(res.items);
        if (res.items.length && !datasetId) setDatasetId(res.items[0].id);
      })
      .catch(() => setError("Could not load datasets. Please sign in and upload one first."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const paramKeys = useMemo(() => Object.keys(params), [params]);

  async function handlePlan() {
    if (!datasetId || !question.trim()) return;
    setPlanning(true);
    setError(null);
    setPlan(null);
    setResult(null);
    setCleanInfo(null);
    try {
      const p = await planIntelligence(datasetId, question.trim());
      setPlan(p);
      const initial: Record<string, string> = {};
      Object.entries(p.parameters || {}).forEach(([k, v]) => {
        initial[k] = v === null || v === undefined ? "" : String(v);
      });
      setParams(initial);
    } catch {
      setError("Could not build a plan for that question. Try rephrasing or pick a dataset.");
    } finally {
      setPlanning(false);
    }
  }

  function buildParamPayload(): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    Object.entries(params).forEach(([k, v]) => {
      if (v === "") return;
      out[k] = k === "poverty_line" ? Number(v) : v;
    });
    return out;
  }

  async function handleRun() {
    if (!plan) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setCleanInfo(null);
    try {
      let targetDataset = datasetId;
      if (autoClean && plan.cleaning_steps.length) {
        const cleaned = await cleanIntelligence(datasetId, plan.cleaning_steps);
        setCleanInfo(cleaned);
        targetDataset = cleaned.cleaned_dataset_id;
      }
      const res = await runIntelligenceAnalysis(plan.endpoint, targetDataset, buildParamPayload());
      if (res.status === "failed") {
        setError(res.error_message || "The analysis could not be completed.");
      } else {
        setResult(res);
      }
    } catch {
      setError("The analysis could not be completed. Check the mapped variables below and try again.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-16">
      <div className="mb-8">
        <span className="inline-block text-xs font-semibold tracking-wide text-white bg-aic-green rounded-full px-3 py-1 mb-3">
          AIC INTELLIGENCE
        </span>
        <h1 className="text-4xl font-bold text-aic-dark mb-3">Ask your data anything</h1>
        <p className="text-aic-muted">
          Type a question about poverty, agriculture, diversification or spatial patterns. AIC Intelligence
          proposes the cleaning and analysis, you confirm, and it runs — or keep using the{" "}
          <Link href="/microdata" className="text-aic-green underline">manual studios</Link>.
        </p>
      </div>

      <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8">
        <label className="block text-sm font-semibold text-aic-dark mb-1">Dataset</label>
        <select
          className="w-full border border-slate-300 rounded-lg px-3 py-2 mb-4"
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
        >
          {datasets.length === 0 && <option value="">No datasets available</option>}
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
              {d.country_iso3 ? ` — ${d.country_iso3}` : ""}
            </option>
          ))}
        </select>

        <label className="block text-sm font-semibold text-aic-dark mb-1">Your question</label>
        <textarea
          className="w-full border border-slate-300 rounded-lg px-3 py-2 h-24"
          placeholder="e.g. What is the poverty rate by district and where are the hotspots?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <div className="flex flex-wrap gap-2 mt-3">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setQuestion(ex)}
              className="text-xs bg-slate-100 hover:bg-slate-200 text-aic-dark rounded-full px-3 py-1"
            >
              {ex}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={handlePlan}
          disabled={planning || !datasetId || !question.trim()}
          className="btn-primary mt-4 disabled:opacity-50"
        >
          {planning ? "Thinking..." : "Build analysis plan"}
        </button>
      </section>

      {error && <p className="text-aic-red mb-6">{error}</p>}

      {plan && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-aic-dark">Proposed plan: {plan.analysis_label}</h2>
            <span className="text-xs text-aic-muted border border-slate-200 rounded-full px-2 py-0.5">
              {plan.engine === "gemini" ? "Gemini" : "AIC engine"}
            </span>
          </div>
          <p className="text-aic-dark mb-4">{plan.rationale}</p>

          {plan.needs_clarification && plan.clarification && (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
              {plan.clarification}
            </p>
          )}

          <h3 className="text-sm font-semibold text-aic-dark mb-2">Variables (edit if needed)</h3>
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            {paramKeys.length === 0 && (
              <p className="text-aic-muted text-sm">Uses this dataset&apos;s saved variable mappings.</p>
            )}
            {paramKeys.map((k) => (
              <div key={k}>
                <label className="block text-xs text-aic-muted mb-1">{k.replace(/_/g, " ")}</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm"
                  type={k === "poverty_line" ? "number" : "text"}
                  value={params[k]}
                  onChange={(e) => setParams({ ...params, [k]: e.target.value })}
                />
              </div>
            ))}
          </div>

          {plan.cleaning_steps.length > 0 && (
            <div className="mb-4">
              <label className="flex items-center gap-2 text-sm font-semibold text-aic-dark mb-2">
                <input type="checkbox" checked={autoClean} onChange={(e) => setAutoClean(e.target.checked)} />
                Clean the data first ({plan.cleaning_steps.length} step{plan.cleaning_steps.length > 1 ? "s" : ""})
              </label>
              <ul className="list-disc list-inside text-sm text-aic-muted space-y-1">
                {plan.cleaning_steps.map((s, i) => (
                  <li key={i}>{s.label}</li>
                ))}
              </ul>
            </div>
          )}

          {plan.warnings.length > 0 && (
            <ul className="text-sm text-amber-700 mb-4 space-y-1">
              {plan.warnings.map((w, i) => (
                <li key={i}>⚠️ {w}</li>
              ))}
            </ul>
          )}

          <button
            type="button"
            onClick={handleRun}
            disabled={running}
            className="btn-primary disabled:opacity-50"
          >
            {running ? "Running analysis..." : autoClean ? "Clean & run analysis" : "Run analysis"}
          </button>
        </section>
      )}

      {cleanInfo && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8">
          <h2 className="text-lg font-semibold text-aic-dark mb-3">Data cleaning report</h2>
          <p className="text-sm text-aic-muted mb-2">
            Saved as <span className="font-medium text-aic-dark">{cleanInfo.cleaned_dataset_name}</span>{" "}
            ({cleanInfo.row_count} rows × {cleanInfo.column_count} columns) — also available in your catalog.
          </p>
          <ul className="list-disc list-inside text-sm text-aic-dark space-y-1">
            {cleanInfo.report.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>
      )}

      {result && (
        <>
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8">
            <h2 className="text-xl font-semibold text-aic-dark mb-3">Results</h2>
            {result.interpretation_text ? (
              <p className="text-aic-dark whitespace-pre-line">{result.interpretation_text}</p>
            ) : (
              <p className="text-aic-muted">Analysis complete. See the full breakdown in the studio view.</p>
            )}
          </section>

          {result.job_id && (
            <section className="mb-10">
              <AIPolicyBriefPanel jobId={result.job_id} defaultTitle={`Policy Brief — ${plan?.analysis_label ?? "analysis"}`} />
            </section>
          )}
        </>
      )}
    </main>
  );
}
