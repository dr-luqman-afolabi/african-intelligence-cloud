"use client";

import { Suspense, useEffect, useState } from "react";
import AIPolicyBriefPanel from "@/components/microdata/AIPolicyBriefPanel";
import { useSearchParams } from "next/navigation";
import { runPovertyAnalysis, type AnalysisResultResponse } from "@/lib/api";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
      <p className="text-sm text-aic-muted mb-1">{label}</p>
      <p className="text-3xl font-bold text-aic-dark">{value}</p>
    </div>
  );
}

function formatPercent(value: unknown) {
  if (typeof value !== "number") return "—";
  return (value * 100).toFixed(1) + "%";
}

function formatNumber(value: unknown, digits = 2) {
  if (typeof value !== "number") return "—";
  return value.toFixed(digits);
}

function PovertyResultsInner() {
  const searchParams = useSearchParams();

  const datasetId = searchParams.get("dataset_id") || "";
  const welfareVariable = searchParams.get("welfare_variable") || "";
  const povertyLine = Number(searchParams.get("poverty_line") || "0");
  const weightVariable = searchParams.get("weight_variable") || undefined;
  const geographyVariable = searchParams.get("geography_variable") || undefined;
  const groupByParam = searchParams.get("group_by") || "";
  const groupBy = groupByParam ? groupByParam.split(",").filter(Boolean) : [];

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId || !welfareVariable || !povertyLine) {
      setError("Missing required analysis parameters.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    runPovertyAnalysis({
      dataset_id: datasetId,
      welfare_variable: welfareVariable,
      poverty_line: povertyLine,
      weight_variable: weightVariable,
      geography_variable: geographyVariable,
      group_by: groupBy,
    })
      .then((res) => {
        if (res.status === "failed") {
          setError(res.error_message || "Analysis failed.");
        } else {
          setResult(res);
        }
      })
      .catch(() => setError("Could not run poverty analysis. Please try again."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, welfareVariable, povertyLine, weightVariable, geographyVariable, groupByParam]);

  const summary = (result?.summary_stats || {}) as Record<string, unknown>;
  const tables = (result?.tables || {}) as Record<string, unknown>;

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-aic-dark mb-4">Poverty Analysis</h1>
      <p className="text-aic-muted mb-10">
        FGT poverty indices and inequality statistics computed from your uploaded microdata.
      </p>

      {loading && <p className="text-aic-muted">Running analysis...</p>}
      {error && <p className="text-aic-red mb-6">{error}</p>}

      {!loading && !error && result && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-10">
            <StatCard label="Poverty headcount" value={formatPercent(summary.headcount)} />
            <StatCard label="Poverty gap" value={formatPercent(summary.poverty_gap)} />
            <StatCard
              label="Squared poverty gap"
              value={formatPercent(summary.squared_poverty_gap)}
            />
            <StatCard label="Gini coefficient" value={formatNumber(summary.gini)} />
          </div>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">Interpretation</h2>
            <p className="text-aic-dark whitespace-pre-line">
              {result.interpretation_text || "No interpretation available."}
            </p>
          </section>
          {result.job_id && (
            <section className="mb-10">
              <AIPolicyBriefPanel jobId={result.job_id} defaultTitle={`Policy Brief — Poverty analysis`} />
            </section>
          )}

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">Summary</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-aic-muted">Mean consumption</p>
                <p className="text-aic-dark font-medium">
                  {formatNumber(summary.mean_consumption)}
                </p>
              </div>
              <div>
                <p className="text-aic-muted">Median consumption</p>
                <p className="text-aic-dark font-medium">
                  {formatNumber(summary.median_consumption)}
                </p>
              </div>
              <div>
                <p className="text-aic-muted">Observations</p>
                <p className="text-aic-dark font-medium">{String(summary.n_obs ?? "—")}</p>
              </div>
            </div>
          </section>

          {groupBy.map((groupVar) => {
            const rows = (tables[groupVar] || []) as Record<string, unknown>[];
            if (!rows.length) return null;
            return (
              <section
                key={groupVar}
                className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10"
              >
                <h2 className="text-xl font-semibold text-aic-dark mb-4">
                  Breakdown by {groupVar}
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="text-aic-muted border-b border-slate-200">
                        <th className="py-2 pr-4">Group</th>
                        <th className="py-2 pr-4">Headcount</th>
                        <th className="py-2 pr-4">Poverty gap</th>
                        <th className="py-2 pr-4">Squared gap</th>
                        <th className="py-2 pr-4">Gini</th>
                        <th className="py-2 pr-4">Obs.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 pr-4">{String(row.group ?? "—")}</td>
                          <td className="py-2 pr-4">{formatPercent(row.headcount)}</td>
                          <td className="py-2 pr-4">{formatPercent(row.poverty_gap)}</td>
                          <td className="py-2 pr-4">{formatPercent(row.squared_poverty_gap)}</td>
                          <td className="py-2 pr-4">{formatNumber(row.gini)}</td>
                          <td className="py-2 pr-4">{String(row.n_obs ?? "—")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            );
          })}

          <button
            onClick={() => window.print()}
            className="bg-aic-dark text-white px-5 py-2 rounded-lg font-medium"
          >
            Export / print report
          </button>
        </>
      )}
    </main>
  );
}

export default function PovertyResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-aic-muted">Loading...</p>
        </main>
      }
    >
      <PovertyResultsInner />
    </Suspense>
  );
}
