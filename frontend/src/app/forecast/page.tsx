"use client";

import { useEffect, useMemo, useState } from "react";
import ForecastChart from "@/components/forecast/ForecastChart";
import AIInsightPanel from "@/components/insights/AIInsightPanel";
import {
  fetchHarvestStatMeta,
  fetchForecast,
  type HarvestStatMeta,
  type ForecastResponse,
} from "@/lib/api";

const MODEL_LABELS: Record<string, string> = {
  ensemble: "Ensemble (recommended)",
  arima: "ARIMA (1,1,1)",
  ets: "Holt exponential smoothing",
  linear: "Linear trend",
};

export default function ForecastPage() {
  const [meta, setMeta] = useState<HarvestStatMeta | null>(null);
  const [country, setCountry] = useState("");
  const [crop, setCrop] = useState("");
  const [metric, setMetric] = useState("yield");
  const [horizon, setHorizon] = useState(5);
  const [model, setModel] = useState("ensemble");

  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHarvestStatMeta()
      .then((m) => {
        setMeta(m);
        if (m.countries.length) setCountry(m.countries.includes("Nigeria") ? "Nigeria" : m.countries[0]);
      })
      .catch(() => setError("Could not load the crop catalog."));
  }, []);

  const crops = useMemo(() => {
    if (!meta || !country) return [];
    return meta.crops_by_country[country] || [];
  }, [meta, country]);

  useEffect(() => {
    if (crops.length) setCrop((prev) => (crops.includes(prev) ? prev : crops.includes("Maize") ? "Maize" : crops[0]));
  }, [crops]);

  async function runForecast() {
    if (!country || !crop) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchForecast({ country, crop, metric, horizon });
      setResult(res);
      if (res.available_models?.length) {
        setModel((m) => (res.available_models!.includes(m) ? m : res.available_models![0]));
      }
      if (res.reason === "too_short")
        setError(`Not enough history to forecast (need ≥ ${res.min_points ?? 6} years). Try another crop or country.`);
      else if (res.reason === "no_data") setError("No data for that country/crop combination.");
    } catch {
      setError("Forecast service is warming up — please try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  const insightSeries = useMemo(() => {
    if (!result?.history?.length) return [];
    return [{
      label: `${result.country} — ${result.crop}`,
      country: result.country,
      crop: result.crop,
      units: result.units,
      points: result.history.map((h) => ({ year: h.year, value: h.value })),
    }];
  }, [result]);

  const fcPoints = result?.models?.[model]?.points || [];

  return (
    <main className="max-w-6xl mx-auto px-4 py-16">
      <div className="mb-8">
        <span className="inline-block text-xs font-semibold tracking-wide text-white bg-aic-green rounded-full px-3 py-1 mb-3">
          FORECASTING
        </span>
        <h1 className="text-4xl font-bold text-aic-dark mb-3">Crop yield & production forecasts</h1>
        <p className="text-aic-muted">
          Project a crop indicator forward with confidence intervals, and compare methods
          (ARIMA, Holt exponential smoothing, linear trend, and an ensemble). Forecasts use the same
          nationally-aggregated HarvestStat-Africa data as the Crop Statistics explorer.
        </p>
      </div>

      {meta && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8 grid gap-4 md:grid-cols-5">
          <div className="md:col-span-2">
            <label className="block text-xs text-aic-muted mb-1">Country</label>
            <select className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm" value={country} onChange={(e) => setCountry(e.target.value)}>
              {meta.countries.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-aic-muted mb-1">Crop</label>
            <select className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm" value={crop} onChange={(e) => setCrop(e.target.value)}>
              {crops.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-aic-muted mb-1">Metric</label>
            <select className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm" value={metric} onChange={(e) => setMetric(e.target.value)}>
              {Object.entries(meta.metrics).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-aic-muted mb-1">Horizon: {horizon} yrs</label>
            <input type="range" min={1} max={15} value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="w-full mt-2" />
          </div>
          <div>
            <label className="block text-xs text-aic-muted mb-1">Model</label>
            <select className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm" value={model} onChange={(e) => setModel(e.target.value)}>
              {(result?.available_models || ["ensemble", "arima", "ets", "linear"]).map((m) => (
                <option key={m} value={m}>{MODEL_LABELS[m] || m}</option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2 flex items-end">
            <button type="button" onClick={runForecast} disabled={loading || !country || !crop} className="btn-primary w-full disabled:opacity-50">
              {loading ? "Forecasting…" : "Run forecast"}
            </button>
          </div>
        </section>
      )}

      {error && <p className="text-aic-red mb-6">{error}</p>}

      {result && result.models && Object.keys(result.models).length > 0 && (
        <>
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h2 className="text-xl font-semibold text-aic-dark mb-1">
              {result.country} — {result.crop}
            </h2>
            <p className="text-sm text-aic-muted mb-4">
              {MODEL_LABELS[model] || model} · {result.units} · next {result.horizon} years · shaded band = 95% interval
            </p>
            <ForecastChart data={result} model={model} />
          </section>

          {fcPoints.length > 0 && (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mt-6 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-aic-muted border-b">
                    <th className="py-2 pr-4">Year</th>
                    <th className="py-2 pr-4">Forecast ({result.units})</th>
                    <th className="py-2 pr-4">Lower 95%</th>
                    <th className="py-2 pr-4">Upper 95%</th>
                  </tr>
                </thead>
                <tbody>
                  {fcPoints.map((p) => (
                    <tr key={p.year} className="border-b last:border-0">
                      <td className="py-1.5 pr-4">{p.year}</td>
                      <td className="py-1.5 pr-4 font-medium text-aic-dark">{p.value}</td>
                      <td className="py-1.5 pr-4 text-aic-muted">{p.lower}</td>
                      <td className="py-1.5 pr-4 text-aic-muted">{p.upper}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {insightSeries.length > 0 && (
            <AIInsightPanel
              title={`${result.country} — ${result.crop} ${result.units}`}
              metric={metric}
              series={insightSeries}
            />
          )}
        </>
      )}
    </main>
  );
}
