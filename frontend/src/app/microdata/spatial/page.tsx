"use client";

import { Suspense, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { runSpatialPovertyAnalysis, type AnalysisResultResponse } from "@/lib/api";

// Leaflet reads `window` at import time — must load client-side only.
const ChoroplethMap = dynamic(() => import("@/components/microdata/ChoroplethMap"), {
  ssr: false,
  loading: () => <div className="h-64 flex items-center justify-center text-aic-muted text-sm">Loading map...</div>,
});

function formatPercent(value: unknown) {
  if (typeof value !== "number") return "—";
  return (value * 100).toFixed(1) + "%";
}

interface MoransI {
  available?: boolean;
  moran_i?: number | null;
  p_value?: number | null;
  method?: string;
  note?: string;
}

function SpatialResultsInner() {
  const searchParams = useSearchParams();

  const datasetId = searchParams.get("dataset_id") || "";
  const geoVariable = searchParams.get("geo_variable") || searchParams.get("geography_variable") || "";
  const welfareVariable = searchParams.get("welfare_variable") || "";
  const povertyLine = Number(searchParams.get("poverty_line") || "0");
  const weightVariable = searchParams.get("weight_variable") || undefined;

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId || !welfareVariable || !povertyLine || !geoVariable) {
      setError("Missing required analysis parameters.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    runSpatialPovertyAnalysis({
      dataset_id: datasetId,
      geo_variable: geoVariable,
      welfare_variable: welfareVariable,
      poverty_line: povertyLine,
      weight_variable: weightVariable,
    })
      .then((res) => {
        if (res.status === "failed") {
          setError(res.error_message || "Spatial analysis failed.");
        } else {
          setResult(res);
        }
      })
      .catch(() => setError("Could not run spatial analysis. Please try again."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, welfareVariable, povertyLine, weightVariable, geoVariable]);

  const charts = (result?.charts || {}) as {
    rankings?: Record<string, unknown>[];
    morans_i?: MoransI;
  };
  const rankings = charts.rankings || [];
  const moransI = charts.morans_i || {};

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-aic-dark mb-4">Spatial Poverty Analysis</h1>
      <p className="text-aic-muted mb-10">
        District and province-level poverty rankings derived from your uploaded microdata,
        with map-ready output for geographic visualization.
      </p>

      {loading && <p className="text-aic-muted">Running spatial analysis...</p>}
      {error && <p className="text-aic-red mb-6">{error}</p>}

      {!loading && !error && result && (
        <>
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">Poverty map</h2>
            {result.geojson && (result.geojson as unknown as GeoJSON.FeatureCollection).features?.length ? (
              <ChoroplethMap
                geojson={result.geojson as unknown as GeoJSON.FeatureCollection}
                valueField="poverty_headcount"
                label="Poverty headcount"
                formatValue={(v) => (v * 100).toFixed(1) + "%"}
              />
            ) : (
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center h-64 text-aic-muted text-sm text-center px-6">
                No boundary geometry was available for this analysis. Upload GADM/OCHA boundaries via
                POST /spatial/boundaries/upload (GeoJSON or zipped shapefile), or pass a GeoJSON file
                when running the analysis, to enable choropleth mapping of poverty rates by{" "}
                {geoVariable || "region"}.
              </div>
            )}
          </section>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">
              Poverty rankings by {geoVariable}
            </h2>
            {rankings.length === 0 ? (
              <p className="text-aic-muted">No ranking data available.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead>
                    <tr className="text-aic-muted border-b border-slate-200">
                      <th className="py-2 pr-4">Region</th>
                      <th className="py-2 pr-4">Headcount</th>
                      <th className="py-2 pr-4">Poverty gap</th>
                      <th className="py-2 pr-4">Squared gap</th>
                      <th className="py-2 pr-4">Gini</th>
                      <th className="py-2 pr-4">Obs.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.map((row, idx) => (
                      <tr key={idx} className="border-b border-slate-100">
                        <td className="py-2 pr-4">{String(row.group ?? "—")}</td>
                        <td className="py-2 pr-4">{formatPercent(row.headcount)}</td>
                        <td className="py-2 pr-4">{formatPercent(row.poverty_gap)}</td>
                        <td className="py-2 pr-4">{formatPercent(row.squared_poverty_gap)}</td>
                        <td className="py-2 pr-4">
                          {typeof row.gini === "number" ? row.gini.toFixed(2) : "—"}
                        </td>
                        <td className="py-2 pr-4">{String(row.n_obs ?? "—")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
            <h2 className="text-xl font-semibold text-aic-dark mb-4">
              Spatial autocorrelation (Moran&apos;s I)
            </h2>
            {moransI.available ? (
              <div className="text-sm text-aic-dark">
                <p>Moran&apos;s I: {moransI.moran_i?.toFixed(3)}</p>
                <p>p-value: {moransI.p_value?.toFixed(3)}</p>
                {moransI.method && <p className="text-aic-muted mt-2">{moransI.method}</p>}
              </div>
            ) : (
              <p className="text-aic-muted text-sm">
                {moransI.note ||
                  "Moran's I is not available for this analysis. Provide a GeoJSON boundary file and ensure PySAL/geopandas are installed to enable spatial autocorrelation statistics."}
              </p>
            )}
          </section>

          {result.interpretation_text && (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
              <h2 className="text-xl font-semibold text-aic-dark mb-4">Interpretation</h2>
              <p className="text-aic-dark whitespace-pre-line">{result.interpretation_text}</p>
            </section>
          )}
        </>
      )}
    </main>
  );
}

export default function SpatialResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-aic-muted">Loading...</p>
        </main>
      }
    >
      <SpatialResultsInner />
    </Suspense>
  );
}
