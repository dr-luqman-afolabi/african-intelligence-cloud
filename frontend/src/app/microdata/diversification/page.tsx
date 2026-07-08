"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { runDiversificationAnalysis, type AnalysisResultResponse } from "@/lib/api";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
      <p className="text-sm text-aic-muted mb-1">{label}</p>
      <p className="text-3xl font-bold text-aic-dark">{value}</p>
    </div>
  );
}

function formatNumber(value: unknown, digits = 2) {
  if (typeof value !== "number") return "—";
  return value.toFixed(digits);
}

function DiversificationResultsInner() {
  const searchParams = useSearchParams();

  const datasetId = searchParams.get("dataset_id") || "";
  const weightVariable = searchParams.get("weight_variable") || undefined;
  const groupByParam = searchParams.get("group_by") || "";
  const groupBy = groupByParam ? groupByParam.split(",").filter(Boolean) : [];
  const cropColumns = (searchParams.get("crop_columns") || "").split(",").filter(Boolean);
  const incomeColumns = (searchParams.get("income_columns") || "").split(",").filter(Boolean);

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId || (cropColumns.length < 2 && incomeColumns.length < 2)) {
      setError("Select a dataset and at least two crop or income source columns.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    runDiversificationAnalysis({
      dataset_id: datasetId,
      crop_columns: cropColumns.length >= 2 ? cropColumns : undefined,
      income_columns: incomeColumns.length >= 2 ? incomeColumns : undefined,
      weight_variable: weightVariable,
      group_by: groupBy,
    })
      .then((res) => {
        if (res.status === "failed") {
          setError(res.error_message || "Diversification analysis failed.");
        } else {
          setResult(res);
        }
      })
      .catch((err) => setError(err?.response?.data?.detail || "Could not run diversification analysis."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, weightVariable, groupByParam, searchParams]);

  const summary = (result?.summary_stats || {}) as Record<string, unknown>;
  const tables = (result?.tables || {}) as Record<string, unknown>;

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-aic-dark mb-4">Diversification Analysis</h1>
      <p className="text-aic-muted mb-10">
        Crop, income, and livelihood diversification indices (Simpson, Shannon, Herfindahl)
        computed from your uploaded microdata.
      </p>

      {loading && <p className="text-aic-muted">Running diversification analysis...</p>}
      {error && <p className="text-aic-red mb-6">{error}</p>}

      {!loading && !error && result && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-10">
            <StatCard label="Mean crop count" value={formatNumber(summary.crop_count, 1)} />
            <StatCard label="Crop Simpson index" value={formatNumber(summary.crop_simpson_index)} />
            <StatCard label="Crop Shannon index" value={formatNumber(summary.crop_shannon_index)} />
            <StatCard label="Crop Herfindahl index" value={formatNumber(summary.crop_herfindahl_index)} />
          </div>

          {(summary.income_diversification_simpson != null || summary.livelihood_diversification_simpson != null) && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-10">
              <StatCard label="Income diversification (Simpson)" value={formatNumber(summary.income_diversification_simpson)} />
              <StatCard label="Income diversification (Shannon)" value={formatNumber(summary.income_diversification_shannon)} />
              <StatCard label="Livelihood diversification (Simpson)" value={formatNumber(summary.livelihood_diversification_simpson)} />
              <StatCard label="Livestock diversification (Simpson)" value={formatNumber(summary.livestock_diversification_simpson)} />
            </div>
          )}

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">Interpretation</h2>
            <p className="text-aic-dark whitespace-pre-line">
              {result.interpretation_text || "No interpretation available."}
            </p>
          </section>

          {groupBy.map((groupVar) => {
            const rows = (tables[groupVar] || []) as Record<string, unknown>[];
            if (!rows.length) return null;
            return (
              <section key={groupVar} className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
                <h2 className="text-xl font-semibold text-aic-dark mb-4">Breakdown by {groupVar}</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="text-aic-muted border-b border-slate-200">
                        <th className="py-2 pr-4">Group</th>
                        <th className="py-2 pr-4">Crop count</th>
                        <th className="py-2 pr-4">Simpson</th>
                        <th className="py-2 pr-4">Shannon</th>
                        <th className="py-2 pr-4">Herfindahl</th>
                        <th className="py-2 pr-4">Obs.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 pr-4">{String(row.group ?? "—")}</td>
                          <td className="py-2 pr-4">{formatNumber(row.crop_count, 1)}</td>
                          <td className="py-2 pr-4">{formatNumber(row.crop_simpson_index)}</td>
                          <td className="py-2 pr-4">{formatNumber(row.crop_shannon_index)}</td>
                          <td className="py-2 pr-4">{formatNumber(row.crop_herfindahl_index)}</td>
                          <td className="py-2 pr-4">{String(row.n_obs ?? "—")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            );
          })}

          <button onClick={() => window.print()} className="bg-aic-dark text-white px-5 py-2 rounded-lg font-medium">
            Export / print report
          </button>
        </>
      )}
    </main>
  );
}

export default function DiversificationResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-aic-muted">Loading...</p>
        </main>
      }
    >
      <DiversificationResultsInner />
    </Suspense>
  );
}
