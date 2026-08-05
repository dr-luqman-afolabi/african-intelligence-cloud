"use client";

import { Suspense, useEffect, useState } from "react";
import AIPolicyBriefPanel from "@/components/microdata/AIPolicyBriefPanel";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  fetchMicrodataAnalysisDefaults,
  fetchMicrodataDatasets,
  fetchMicrodataVariables,
  runSpatialPovertyAnalysis,
  type AnalysisResultResponse,
  type MicrodataDataset,
  type MicrodataVariable,
} from "@/lib/api";
import { AFRICAN_COUNTRIES, ADMIN_LEVELS } from "@/lib/africaCountries";

// Leaflet reads `window` at import time — must load client-side only.
const ChoroplethMap = dynamic(() => import("@/components/microdata/ChoroplethMap"), {
  ssr: false,
  loading: () => <div className="h-64 flex items-center justify-center text-aic-muted text-sm">Loading map...</div>,
});

function formatPercent(value: unknown) {
  if (typeof value !== "number") return "—";
  return (value * 100).toFixed(1) + "%";
}

function normalizedVariableName(variable: MicrodataVariable) {
  return `${variable.variable_name} ${variable.variable_label || ""}`.toLowerCase().replace(/[^a-z0-9]+/g, "_");
}

function findVariable(variables: MicrodataVariable[], candidates: string[]) {
  for (const candidate of candidates) {
    const exact = variables.find((variable) => variable.variable_name.toLowerCase() === candidate);
    if (exact) return exact.variable_name;
  }
  for (const candidate of candidates) {
    const partial = variables.find((variable) => normalizedVariableName(variable).includes(candidate));
    if (partial) return partial.variable_name;
  }
  return "";
}

function suggestSpatialVariables(variables: MicrodataVariable[], adminLevel: string) {
  const geographyCandidates: Record<string, string[]> = {
    ADM1: ["province", "region", "state", "adm1"],
    ADM2: ["district", "county", "adm2"],
    ADM3: ["sector", "subdistrict", "commune", "adm3"],
    ADM0: ["country", "iso3", "adm0"],
  };
  return {
    geography: findVariable(variables, geographyCandidates[adminLevel] || geographyCandidates.ADM2),
    welfare: findVariable(variables, [
      "cons1ae", "welfare", "consumption_per_adult", "consumption", "expenditure", "exp9", "income",
    ]),
    weight: findVariable(variables, ["pop_wt", "weight", "survey_weight", "hhweight", "sample_weight"]),
  };
}

function isIdentifierVariable(name: string) {
  return ["hhid", "household_id", "person_id", "pid", "uuid", "record_id"].includes(name.toLowerCase());
}

function getAnalysisErrorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  return error instanceof Error && error.message
    ? error.message
    : "Could not run spatial analysis. Please try again.";
}

interface MoransI {
  available?: boolean;
  moran_i?: number | null;
  p_value?: number | null;
  method?: string;
  note?: string;
}

function SpatialSetup() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [variables, setVariables] = useState<MicrodataVariable[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [geoVariable, setGeoVariable] = useState("");
  const [welfareVariable, setWelfareVariable] = useState("");
  const [weightVariable, setWeightVariable] = useState("");
  const [countryIso3, setCountryIso3] = useState("RWA");
  const [adminLevel, setAdminLevel] = useState("ADM1");
  const [povertyLine, setPovertyLine] = useState(100);
  const [loading, setLoading] = useState(true);
  const [variablesLoading, setVariablesLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchMicrodataDatasets(0, 500)
      .then((response) => {
        setDatasets(response.items);
        if (response.items[0]) {
          setDatasetId(response.items[0].id);
          if (response.items[0].country_iso3) setCountryIso3(response.items[0].country_iso3);
        }
      })
      .catch(() => setError("Sign in to access analysis-ready datasets."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!datasetId) {
      setVariables([]);
      return;
    }
    setVariablesLoading(true);
    setGeoVariable("");
    setWelfareVariable("");
    setWeightVariable("");
    Promise.all([
      fetchMicrodataVariables(datasetId),
      fetchMicrodataAnalysisDefaults(datasetId).catch(() => null),
    ])
      .then(([items, defaults]) => {
        setVariables(items);
        const suggested = suggestSpatialVariables(items, adminLevel);
        setGeoVariable(
          (adminLevel === "ADM1" ? defaults?.province_variable : defaults?.district_variable)
            || suggested.geography,
        );
        setWelfareVariable(defaults?.welfare_variable || suggested.welfare);
        setWeightVariable(defaults?.weight_variable || suggested.weight);
        if (typeof defaults?.poverty_line === "number" && defaults.poverty_line > 0) {
          setPovertyLine(defaults.poverty_line);
        }
      })
      .catch(() => setError("The variables for this dataset could not be loaded."))
      .finally(() => setVariablesLoading(false));
    const selected = datasets.find((item) => item.id === datasetId);
    if (selected?.country_iso3) setCountryIso3(selected.country_iso3);
    // `adminLevel` is read for the initial suggestion but deliberately excluded
    // from the deps: re-running this on an admin-level change would refetch the
    // variable list and wipe the user's picks. The level dropdown's onChange
    // re-suggests the geography variable on its own instead.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, datasets]);

  function launch() {
    if (!datasetId || !geoVariable || !welfareVariable || povertyLine <= 0) {
      setError("Select a dataset, geography variable, welfare variable and a positive poverty line.");
      return;
    }
    if (isIdentifierVariable(geoVariable)) {
      const suggested = suggestSpatialVariables(variables, adminLevel).geography;
      setError(
        suggested
          ? `"${geoVariable}" is an identifier, not a map geography. Use "${suggested}" for ${adminLevel}.`
          : `"${geoVariable}" is an identifier, not a map geography. Select a province, region or district field.`,
      );
      if (suggested) setGeoVariable(suggested);
      return;
    }
    const params = new URLSearchParams({
      dataset_id: datasetId,
      geo_variable: geoVariable,
      welfare_variable: welfareVariable,
      poverty_line: String(povertyLine),
      country_iso3: countryIso3,
      admin_level: adminLevel,
    });
    if (weightVariable) params.set("weight_variable", weightVariable);
    router.push(`/microdata/spatial?${params.toString()}`);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:py-14">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-widest text-blue-600">Guided spatial workflow</p>
        <h1 className="mt-2 text-3xl font-bold text-aic-dark sm:text-4xl">Build a poverty map</h1>
        <p className="mt-3 max-w-3xl text-aic-muted">
          Choose the microdata variables and administrative boundary level. AIC automatically retrieves
          country boundaries, joins regional estimates and opens the choropleth when analysis finishes.
        </p>
      </div>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="mb-6 grid grid-cols-3 gap-2 text-center text-xs font-semibold">
          <div className="rounded-lg bg-blue-600 px-2 py-3 text-white">1. Configure</div>
          <div className="rounded-lg bg-slate-100 px-2 py-3 text-slate-500">2. Analyze</div>
          <div className="rounded-lg bg-slate-100 px-2 py-3 text-slate-500">3. Explore map</div>
        </div>
        {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <div className="grid gap-5 md:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">Dataset
            <select value={datasetId} onChange={(event) => setDatasetId(event.target.value)} disabled={loading} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3">
              <option value="">{loading ? "Loading datasets…" : "Select a dataset…"}</option>
              {datasets.map((item) => <option key={item.id} value={item.id}>{item.name}{item.country_iso3 ? ` — ${item.country_iso3}` : ""}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Country boundaries
            <select value={countryIso3} onChange={(event) => setCountryIso3(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3">
              {AFRICAN_COUNTRIES.map((item) => <option key={item.iso3} value={item.iso3}>{item.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Geography variable
            <select value={geoVariable} onChange={(event) => setGeoVariable(event.target.value)} disabled={!datasetId || variablesLoading} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 disabled:bg-slate-50">
              <option value="">{variablesLoading ? "Loading variables…" : "Select district/region field…"}</option>
              {variables.map((item) => <option key={item.id} value={item.variable_name}>{item.variable_label ? `${item.variable_label} — ` : ""}{item.variable_name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Administrative level
            <select value={adminLevel} onChange={(event) => {
              const nextLevel = event.target.value;
              setAdminLevel(nextLevel);
              const suggested = suggestSpatialVariables(variables, nextLevel).geography;
              if (suggested) setGeoVariable(suggested);
            }} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3">
              {ADMIN_LEVELS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Welfare variable
            <select value={welfareVariable} onChange={(event) => setWelfareVariable(event.target.value)} disabled={!datasetId || variablesLoading} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 disabled:bg-slate-50">
              <option value="">Select consumption/income field…</option>
              {variables.map((item) => <option key={item.id} value={item.variable_name}>{item.variable_label ? `${item.variable_label} — ` : ""}{item.variable_name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Weight variable (optional)
            <select value={weightVariable} onChange={(event) => setWeightVariable(event.target.value)} disabled={!datasetId || variablesLoading} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 disabled:bg-slate-50">
              <option value="">No survey weight</option>
              {variables.map((item) => <option key={item.id} value={item.variable_name}>{item.variable_label ? `${item.variable_label} — ` : ""}{item.variable_name}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Poverty line
            <input type="number" min="0.01" step="0.01" value={povertyLine} onChange={(event) => setPovertyLine(Number(event.target.value))} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-3" />
          </label>
        </div>
        {variables.length > 0 && geoVariable && welfareVariable && (
          <p className="mt-5 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            Suggested automatically: {geoVariable} for {adminLevel}, {welfareVariable} for welfare
            {weightVariable ? `, and ${weightVariable} for survey weights` : ""}. You can override these selections.
          </p>
        )}
        <div className="mt-7 flex flex-wrap items-center justify-between gap-3">
          <Link href="/microdata" className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium">Back to Microdata Studio</Link>
          <button onClick={launch} disabled={!datasetId || !geoVariable || !welfareVariable || povertyLine <= 0} className="rounded-lg bg-aic-green px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40">Run analysis and open map →</button>
        </div>
      </section>
    </main>
  );
}

function SpatialResultsInner() {
  const searchParams = useSearchParams();

  const datasetId = searchParams.get("dataset_id") || "";
  const geoVariable = searchParams.get("geo_variable") || searchParams.get("geography_variable") || "";
  const welfareVariable = searchParams.get("welfare_variable") || "";
  const povertyLine = Number(searchParams.get("poverty_line") || "0");
  const weightVariable = searchParams.get("weight_variable") || undefined;
  const countryIso3 = searchParams.get("country_iso3") || undefined;
  const adminLevel = searchParams.get("admin_level") || "ADM2";
  const hasRequiredParameters = Boolean(datasetId && geoVariable && welfareVariable && povertyLine > 0);

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasRequiredParameters) {
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
      country_iso3: countryIso3,
      admin_level: adminLevel,
    })
      .then((res) => {
        if (res.status === "failed") {
          setError(res.error_message || "Spatial analysis failed.");
        } else {
          setResult(res);
        }
      })
      .catch((analysisError) => setError(getAnalysisErrorMessage(analysisError)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, welfareVariable, povertyLine, weightVariable, geoVariable, countryIso3, adminLevel, hasRequiredParameters]);

  if (!hasRequiredParameters) return <SpatialSetup />;

  const charts = (result?.charts || {}) as {
    rankings?: Record<string, unknown>[];
    morans_i?: MoransI;
  };
  const rankings = charts.rankings || [];
  const moransI = charts.morans_i || {};

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl font-bold text-aic-dark">Spatial Poverty Analysis</h1>
        <Link href="/microdata/spatial" className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium">New spatial analysis</Link>
      </div>
      <p className="text-aic-muted mb-10">
        District and province-level poverty rankings derived from your uploaded microdata,
        with map-ready output for geographic visualization.
      </p>

      {loading && (
        <section className="rounded-2xl border border-blue-100 bg-blue-50 p-6">
          <div className="flex items-center gap-4">
            <span className="grid h-12 w-12 animate-pulse place-items-center rounded-full bg-blue-600 text-xl text-white">⌖</span>
            <div><p className="font-semibold text-blue-950">Building your map automatically…</p><p className="mt-1 text-sm text-blue-700">Computing regional poverty, retrieving {countryIso3} {adminLevel} boundaries and joining the results.</p></div>
          </div>
        </section>
      )}
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
                AIC could not match the selected geography values to the automatic {countryIso3} {adminLevel}
                boundaries. Confirm that the geography field contains recognizable district or region names,
                then start a new spatial analysis with the correct administrative level.
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
                        <td className="py-2 pr-4">{String(row.group ?? row.geo_value ?? row[geoVariable] ?? "—")}</td>
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

          {result.job_id && (
            <section className="mb-10">
              <AIPolicyBriefPanel jobId={result.job_id} defaultTitle={`Policy Brief — Spatial analysis`} />
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
