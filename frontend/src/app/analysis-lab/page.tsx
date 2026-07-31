"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  cleanIntelligence,
  fetchMicrodataDatasets,
  planIntelligence,
  runIntelligenceAnalysis,
  type AnalysisResultResponse,
  type IntelligenceCleanResponse,
  type IntelligencePlan,
  type MicrodataDataset,
} from "@/lib/api";

type Stage = "data" | "quality" | "plan" | "execute" | "results";
type Engine = "automatic" | "python" | "r" | "both";

const STEPS: { id: Stage; label: string }[] = [
  { id: "data", label: "Data" },
  { id: "quality", label: "Quality" },
  { id: "plan", label: "Analysis plan" },
  { id: "execute", label: "Execute" },
  { id: "results", label: "Results" },
];

const QUESTIONS = [
  "Estimate the effect of rainfall, fertiliser use and access to credit on agricultural productivity.",
  "What is the poverty rate by district and where are the hotspots?",
  "How diversified are household incomes, and which groups are most vulnerable?",
];

function StepIcon({ done, number }: { done: boolean; number: number }) {
  return (
    <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full border text-xs font-bold ${done ? "border-aic-green bg-aic-green text-white" : "border-slate-300 bg-white text-slate-500"}`}>
      {done ? "✓" : String(number).padStart(2, "0")}
    </span>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return <div role="alert" className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{message}</div>;
}

export default function AnalysisLabPage() {
  const [stage, setStage] = useState<Stage>("data");
  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [question, setQuestion] = useState(QUESTIONS[0]);
  const [engine, setEngine] = useState<Engine>("automatic");
  const [plan, setPlan] = useState<IntelligencePlan | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [approved, setApproved] = useState(false);
  const [autoClean, setAutoClean] = useState(true);
  const [cleanInfo, setCleanInfo] = useState<IntelligenceCleanResponse | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMicrodataDatasets(0, 100)
      .then((response) => {
        setDatasets(response.items);
        if (response.items.length) setDatasetId(response.items[0].id);
      })
      .catch(() => setError("Could not load your datasets. Sign in or upload a dataset first."))
      .finally(() => setLoading(false));
  }, []);

  const selected = useMemo(() => datasets.find((item) => item.id === datasetId), [datasets, datasetId]);
  const currentIndex = STEPS.findIndex((item) => item.id === stage);

  async function buildPlan() {
    if (!datasetId || !question.trim()) return;
    setPlanning(true);
    setError("");
    setApproved(false);
    setResult(null);
    try {
      const proposed = await planIntelligence(datasetId, question.trim());
      setPlan(proposed);
      setParams(Object.fromEntries(Object.entries(proposed.parameters || {}).map(([key, value]) => [key, value == null ? "" : String(value)])));
      setStage("plan");
    } catch {
      setError("AIC could not build a defensible plan for this question. Rephrase it or verify the dataset mappings.");
    } finally {
      setPlanning(false);
    }
  }

  function parameterPayload() {
    return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== "").map(([key, value]) => [key, key === "poverty_line" ? Number(value) : value]));
  }

  async function runAnalysis() {
    if (!plan || !approved) return;
    setRunning(true);
    setError("");
    setResult(null);
    setCleanInfo(null);
    setStage("execute");
    try {
      let targetDataset = datasetId;
      if (autoClean && plan.cleaning_steps.length) {
        const cleaned = await cleanIntelligence(datasetId, plan.cleaning_steps);
        setCleanInfo(cleaned);
        targetDataset = cleaned.cleaned_dataset_id;
      }
      const response = await runIntelligenceAnalysis(plan.endpoint, targetDataset, {
        ...parameterPayload(),
        requested_engine: engine,
      });
      if (response.status === "failed") throw new Error(response.error_message || "Analysis failed");
      setResult(response);
      setStage("results");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The analysis could not be completed. Review the variable mapping and try again.");
      setStage("plan");
    } finally {
      setRunning(false);
    }
  }

  const downloadablePlan = JSON.stringify({ dataset_id: datasetId, question, engine, plan, parameters: parameterPayload(), approved }, null, 2);
  function downloadPlan() {
    const url = URL.createObjectURL(new Blob([downloadablePlan], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "aic-analysis-plan.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-10 sm:px-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="section-label mb-3">Reproducible research</p>
            <h1 className="text-3xl font-bold tracking-tight text-aic-dark sm:text-4xl">Automated Analysis Lab</h1>
            <p className="mt-3 text-base leading-7 text-aic-muted">From raw data to defensible evidence. Review every methodological choice before a single analysis runs.</p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 ring-4 ring-emerald-100" />
            <div><p className="text-sm font-semibold text-emerald-900">Secure runtime available</p><p className="text-xs text-emerald-700">Authenticated · isolated · auditable</p></div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <nav aria-label="Analysis progress" className="card mb-6 overflow-x-auto px-5 py-5">
          <ol className="flex min-w-[650px] items-center">
            {STEPS.map((item, index) => (
              <li key={item.id} className="flex flex-1 items-center">
                <button type="button" onClick={() => index <= currentIndex && setStage(item.id)} className={`flex items-center gap-2 text-sm font-semibold ${index <= currentIndex ? "text-aic-dark" : "text-slate-400"}`}>
                  <StepIcon done={index < currentIndex} number={index + 1} />{item.label}
                </button>
                {index < STEPS.length - 1 && <span className={`mx-4 h-px flex-1 ${index < currentIndex ? "bg-aic-green" : "bg-slate-200"}`} />}
              </li>
            ))}
          </ol>
        </nav>

        {error && <ErrorBanner message={error} />}

        {stage === "data" && (
          <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div className="card p-6 sm:p-8">
              <p className="section-label">01 · Select data</p>
              <h2 className="mt-2 text-2xl font-bold text-aic-dark">Choose a research dataset</h2>
              <p className="mt-2 text-sm text-aic-muted">The lab uses datasets already protected by your AIC account and privacy settings.</p>
              <label className="mt-7 block text-sm font-semibold text-aic-dark">Dataset</label>
              <select className="input-field mt-2" value={datasetId} onChange={(event) => setDatasetId(event.target.value)} disabled={loading}>
                {loading && <option>Loading datasets…</option>}
                {!loading && !datasets.length && <option value="">No datasets available</option>}
                {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}{dataset.country_iso3 ? ` — ${dataset.country_iso3}` : ""}</option>)}
              </select>
              {selected && <div className="mt-5 grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-4"><div><p className="text-xs text-aic-muted">Rows</p><p className="font-bold text-aic-dark">{selected.row_count?.toLocaleString() ?? "Pending"}</p></div><div><p className="text-xs text-aic-muted">Columns</p><p className="font-bold text-aic-dark">{selected.column_count ?? "Pending"}</p></div><div><p className="text-xs text-aic-muted">Country</p><p className="font-bold text-aic-dark">{selected.country_iso3 || "—"}</p></div><div><p className="text-xs text-aic-muted">Status</p><p className="font-bold capitalize text-emerald-700">{selected.status}</p></div></div>}
              <div className="mt-6 flex flex-wrap gap-3"><button className="btn-primary" disabled={!datasetId} onClick={() => setStage("quality")}>Review data quality →</button><Link className="btn-secondary" href="/microdata">Upload or map data</Link></div>
            </div>
            <aside className="rounded-2xl bg-aic-dark p-6 text-white"><h2 className="text-lg font-bold">Before analysis</h2><ul className="mt-5 space-y-5 text-sm"><li><strong className="block">Remove direct identifiers</strong><span className="mt-1 block text-slate-400">Do not include names, phone numbers or exact addresses.</span></li><li><strong className="block">Confirm research authority</strong><span className="mt-1 block text-slate-400">Ensure the project permits this use of the dataset.</span></li><li><strong className="block">Inspect variable mappings</strong><span className="mt-1 block text-slate-400">Automated recommendations depend on meaningful metadata.</span></li></ul><Link href="/privacy" className="mt-7 inline-block text-sm font-semibold text-emerald-300">Data protection policy →</Link></aside>
          </section>
        )}

        {stage === "quality" && (
          <section className="card p-6 sm:p-8">
            <p className="section-label">02 · Quality gate</p><div className="mt-2 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h2 className="text-2xl font-bold text-aic-dark">Automated quality report</h2><p className="mt-1 text-sm text-aic-muted">{selected?.name}</p></div><span className={`badge ${selected?.status === "ready" || selected?.status === "profiled" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{selected?.status || "unknown"}</span></div>
            <div className="mt-7 grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-4"><article className="bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-aic-muted">Observations</p><p className="mt-2 text-2xl font-bold text-aic-dark">{selected?.row_count?.toLocaleString() ?? "—"}</p></article><article className="bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-aic-muted">Variables</p><p className="mt-2 text-2xl font-bold text-aic-dark">{selected?.column_count ?? "—"}</p></article><article className="bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-aic-muted">Privacy</p><p className="mt-2 text-2xl font-bold capitalize text-aic-dark">Private</p></article><article className="bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-aic-muted">Profiling</p><p className="mt-2 text-2xl font-bold capitalize text-emerald-700">{selected?.status}</p></article></div>
            <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">AIC will validate required variables again before execution. Missing-data treatment remains visible in the proposed plan.</div>
            <div className="mt-6 flex justify-end"><button className="btn-primary" onClick={() => setStage("plan")}>Define research question →</button></div>
          </section>
        )}

        {stage === "plan" && (
          <section className="grid gap-6 lg:grid-cols-2">
            <div className="card p-6 sm:p-8"><p className="section-label">03 · Research design</p><h2 className="mt-2 text-2xl font-bold text-aic-dark">Describe your question</h2><label className="mt-6 block text-sm font-semibold text-aic-dark">Research question</label><textarea className="input-field mt-2 min-h-28 resize-y" value={question} onChange={(event) => setQuestion(event.target.value)} />
              <div className="mt-3 flex flex-wrap gap-2">{QUESTIONS.slice(1).map((example) => <button key={example} type="button" onClick={() => setQuestion(example)} className="rounded-full bg-slate-100 px-3 py-1.5 text-left text-xs text-slate-600 hover:bg-slate-200">{example}</button>)}</div>
              <label className="mt-6 block text-sm font-semibold text-aic-dark">Preferred engine</label><select className="input-field mt-2" value={engine} onChange={(event) => setEngine(event.target.value as Engine)}><option value="automatic">Automatic — AIC selects the specialist engine</option><option value="python">Python</option><option value="r">R</option><option value="both">Run both and compare</option></select>
              <button className="btn-primary mt-6" disabled={planning || !question.trim()} onClick={buildPlan}>{planning ? "Building defensible plan…" : plan ? "Refresh analysis plan" : "Build analysis plan"}</button>
            </div>

            <div className="card overflow-hidden"><div className="bg-aic-dark px-6 py-5 text-white"><p className="text-xs font-bold uppercase tracking-widest text-emerald-300">AIC recommendation</p><h2 className="mt-2 text-xl font-bold">{plan?.analysis_label || "Awaiting research question"}</h2></div>
              {!plan ? <div className="p-8 text-sm leading-6 text-aic-muted">Build a plan to see the proposed method, variable mapping, cleaning decisions, warnings and execution engine.</div> : <div className="p-6">
                <p className="text-sm leading-6 text-aic-dark">{plan.rationale}</p>
                <dl className="mt-5 divide-y divide-slate-100 text-sm"><div className="flex justify-between gap-4 py-3"><dt className="text-aic-muted">Method</dt><dd className="font-semibold text-right text-aic-dark">{plan.analysis_label}</dd></div><div className="flex justify-between gap-4 py-3"><dt className="text-aic-muted">Engine</dt><dd className="font-semibold uppercase text-aic-dark">{engine === "automatic" ? plan.engine : engine}</dd></div><div className="flex justify-between gap-4 py-3"><dt className="text-aic-muted">Cleaning steps</dt><dd className="font-semibold text-aic-dark">{plan.cleaning_steps.length}</dd></div></dl>
                {Object.keys(params).length > 0 && <div className="mt-5"><h3 className="text-sm font-semibold text-aic-dark">Mapped parameters</h3><div className="mt-3 grid gap-3 sm:grid-cols-2">{Object.keys(params).map((key) => <label key={key} className="text-xs text-aic-muted">{key.replace(/_/g, " ")}<input className="input-field mt-1 !py-2" value={params[key]} onChange={(event) => setParams({ ...params, [key]: event.target.value })} /></label>)}</div></div>}
                {plan.cleaning_steps.length > 0 && <label className="mt-5 flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm"><input className="mt-1 accent-aic-green" type="checkbox" checked={autoClean} onChange={(event) => setAutoClean(event.target.checked)} /><span><strong className="block text-aic-dark">Apply {plan.cleaning_steps.length} proposed cleaning step{plan.cleaning_steps.length === 1 ? "" : "s"}</strong><span className="text-aic-muted">A cleaned derivative is retained in your catalog.</span></span></label>}
                <div className="mt-5 rounded-xl border-l-4 border-amber-400 bg-amber-50 p-4 text-sm text-amber-900"><strong className="block">Causal claim not automatically permitted</strong><span className="mt-1 block text-xs leading-5 text-amber-800">Treat estimates as associational unless the research design establishes identification assumptions.</span></div>
                {plan.warnings.map((warning) => <p key={warning} className="mt-3 text-xs text-amber-700">⚠ {warning}</p>)}
                <label className="mt-5 flex items-start gap-3 text-sm"><input className="mt-1 accent-aic-green" type="checkbox" checked={approved} onChange={(event) => setApproved(event.target.checked)} /><span><strong className="block text-aic-dark">I reviewed and approve this plan</strong><span className="text-xs text-aic-muted">Execution requires explicit approval.</span></span></label>
                <div className="mt-5 flex gap-3"><button className="btn-primary flex-1" disabled={!approved || running} onClick={runAnalysis}>Approve and run</button><button className="btn-secondary !px-3" onClick={downloadPlan} aria-label="Download plan">↓</button></div>
              </div>}
            </div>
          </section>
        )}

        {stage === "execute" && <section className="card mx-auto max-w-3xl p-8 text-center"><div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-2xl text-emerald-700 animate-pulse">✦</div><h2 className="mt-5 text-2xl font-bold text-aic-dark">Analysis running in a protected environment</h2><p className="mt-2 text-sm text-aic-muted">Validating inputs, applying approved cleaning, fitting the model and producing diagnostics.</p><div className="mx-auto mt-7 max-w-xl rounded-xl bg-aic-dark p-5 text-left font-mono text-xs leading-7 text-slate-300"><p className="text-emerald-300">✓ Dataset authorization verified</p><p className="text-emerald-300">✓ Plan signature recorded</p><p className="text-emerald-300">✓ Network-isolated analysis started</p><p className="animate-pulse text-white">● Computing results and diagnostics…</p></div></section>}

        {stage === "results" && result && (
          <section><div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="section-label">Analysis complete</p><h2 className="mt-2 text-2xl font-bold text-aic-dark">{plan?.analysis_label}</h2><p className="mt-1 text-sm text-aic-muted">Run ID: {result.job_id || "completed"}</p></div><div className="flex gap-3"><button className="btn-secondary" onClick={downloadPlan}>Download plan</button><button className="btn-primary" onClick={() => setStage("plan")}>Refine analysis</button></div></div>
            <div className="grid gap-6 lg:grid-cols-[1fr_320px]"><article className="card p-6 sm:p-8"><div className="flex items-center justify-between"><h3 className="text-xl font-bold text-aic-dark">Evidence summary</h3><span className="badge bg-emerald-100 text-emerald-800">AI assisted</span></div><p className="mt-5 whitespace-pre-line text-sm leading-7 text-slate-700">{result.interpretation_text || "Analysis completed successfully. Open the relevant studio to inspect the complete statistical output."}</p><div className="mt-6 rounded-xl border-l-4 border-amber-400 bg-amber-50 p-4 text-sm text-amber-900"><strong>Interpret with care.</strong> Confirm sample size, missing-data treatment, model assumptions and identification before reporting findings.</div>{cleanInfo && <div className="mt-6"><h4 className="font-semibold text-aic-dark">Cleaning record</h4><ul className="mt-2 list-inside list-disc text-sm text-aic-muted">{cleanInfo.report.map((line) => <li key={line}>{line}</li>)}</ul></div>}</article>
              <aside className="card p-6"><h3 className="font-bold text-aic-dark">Reproducibility record</h3><dl className="mt-4 divide-y divide-slate-100 text-sm"><div className="flex justify-between py-3"><dt className="text-aic-muted">Dataset</dt><dd className="max-w-36 truncate font-semibold text-aic-dark">{selected?.name}</dd></div><div className="flex justify-between py-3"><dt className="text-aic-muted">Engine</dt><dd className="font-semibold uppercase text-aic-dark">{engine === "automatic" ? plan?.engine : engine}</dd></div><div className="flex justify-between py-3"><dt className="text-aic-muted">Status</dt><dd className="font-semibold text-emerald-700">Completed</dd></div><div className="flex justify-between py-3"><dt className="text-aic-muted">Approval</dt><dd className="font-semibold text-aic-dark">Recorded</dd></div></dl><button className="btn-secondary mt-5 w-full" onClick={downloadPlan}>Download JSON plan</button></aside></div>
          </section>
        )}
      </div>
    </main>
  );
}
