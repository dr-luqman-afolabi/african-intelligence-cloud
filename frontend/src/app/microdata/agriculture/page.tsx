"use client";

import { Suspense, useEffect, useState } from "react";
import AIPolicyBriefPanel from "@/components/microdata/AIPolicyBriefPanel";
import { useSearchParams } from "next/navigation";
import { runAgricultureAnalysis, type AnalysisResultResponse } from "@/lib/api";

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

function formatPercent(value: unknown) {
  if (typeof value !== "number") return "—";
  return (value * 100).toFixed(1) + "%";
}

const GROUP_COLUMNS: { key: string; label: string; format: (v: unknown) => string }[] = [
  { key: "crop_yield", label: "Crop yield", format: formatNumber },
  { key: "land_productivity", label: "Land productivity", format: formatNumber },
  { key: "value_of_production", label: "Value of production", format: formatNumber },
  { key: "fertilizer_adoption_rate", label: "Fertilizer", format: formatPercent },
  { key: "irrigation_access_rate", label: "Irrigation", format: formatPercent },
  { key: "n_obs", label: "Obs.", format: (v) => String(v ?? "—") },
];

function AgricultureResultsInner() {
  const searchParams = useSearchParams();

  const datasetId = searchParams.get("dataset_id") || "";
  const weightVariable = searchParams.get("weight_variable") || undefined;
  const groupByParam = searchParams.get("group_by") || "";
  const groupBy = groupByParam ? groupByParam.split(",").filter(Boolean) : [];

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) {
      setError("Missing required analysis parameters.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    runAgricultureAnalysis({ dataset_id: datasetId, weight_variable: weightVariable, group_by: groupBy })
      .then((res) => {
        if (res.status === "failed") {
          setError(res.error_message || "Agriculture analysis failed.");
        } else {
          setResult(res);
        }
      })
      .catch((err) =>
        setError(
          err?.response?.data?.detail ||
            "Could not run agriculture analysis. Make sure this dataset has a saved variable mapping (land_area, crop_output, crop_value, ...)."
        )
      )
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, weightVariable, groupByParam]);

  const summary = (result?.summary_stats || {}) as Record<string, unknown>;
  const tables = (result?.tables || {}) as Record<string, unknown>;

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-aic-dark mb-4">Agriculture Analysis</h1>
      <p className="text-aic-muted mb-10">
        Farm productivity, input adoption, and market participation computed from your uploaded
        microdata via the standard variable mapping.
      </p>

      {loading && <p className="text-aic-muted">Running agriculture analysis...</p>}
      {error && <p className="text-aic-red mb-6">{error}</p>}

      {!loading && !error && result && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-10">
            <StatCard label="Crop yield" value={formatNumber(summary.crop_yield)} />
            <StatCard label="Land productivity" value={formatNumber(summary.land_productivity)} />
            <StatCard label="Fertilizer adoption" value={formatPercent(summary.fertilizer_adoption_rate)} />
            <StatCard label="Market participation" value={formatPercent(summary.market_participation_rate)} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 mb-10">
            <StatCard label="Value of production" value={formatNumber(summary.value_of_production)} />
            <StatCard label="Labour productivity" value={formatNumber(summary.labour_productivity)} />
            <StatCard label="Improved seed" value={formatPercent(summary.improved_seed_adoption_rate)} />
            <StatCard label="Extension access" value={formatPercent(summary.extension_access_rate)} />
          </div>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">Interpretation</h2>
            <p className="text-aic-dark whitespace-pre-line">
              {result.interpretation_text || "No interpretation available."}
            </p>
          </section>
          {result.job_id && (
            <section className="mb-10">
              <AIPolicyBriefPanel jobId={result.job_id} defaultTitle={`Policy Brief — Agriculture analysis`} />
            </section>
          )}

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
                        {GROUP_COLUMNS.map((c) => (
                          <th key={c.key} className="py-2 pr-4">{c.label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-100">
                          <td className="py-2 pr-4">{String(row.group ?? "—")}</td>
                          {GROUP_COLUMNS.map((c) => (
                            <td key={c.key} className="py-2 pr-4">{c.format(row[c.key])}</td>
                          ))}
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

export default function AgricultureResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-aic-muted">Loading...</p>
        </main>
      }
    >
      <AgricultureResultsInner />
    </Suspense>
  );
}
