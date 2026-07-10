"use client";

import { useEffect, useMemo, useState } from "react";
import MultiSeriesLineChart from "@/components/microdata/MultiSeriesLineChart";
import AIInsightPanel from "@/components/insights/AIInsightPanel";
import {
  fetchHarvestStatMeta,
  fetchHarvestStatSeries,
  type HarvestStatMeta,
  type HarvestStatSeriesResponse,
} from "@/lib/api";

function toggle(list: string[], value: string, cap = 999): string[] {
  if (list.includes(value)) return list.filter((v) => v !== value);
  if (list.length >= cap) return list;
  return [...list, value];
}

export default function CropStatisticsPage() {
  const [meta, setMeta] = useState<HarvestStatMeta | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [countries, setCountries] = useState<string[]>([]);
  const [crops, setCrops] = useState<string[]>([]);
  const [metric, setMetric] = useState("yield");
  const [season, setSeason] = useState("");

  const [result, setResult] = useState<HarvestStatSeriesResponse | null>(null);
  const [plotting, setPlotting] = useState(false);

  useEffect(() => {
    fetchHarvestStatMeta()
      .then((m) => {
        setMeta(m);
        if (m.countries.length) setCountries(m.countries.slice(0, 3));
        if (!m.loaded) setError("The crop dataset is still loading on the server — try again in a moment.");
      })
      .catch(() => setError("Could not load the crop statistics catalog."))
      .finally(() => setLoadingMeta(false));
  }, []);

  // Crops available for the currently selected countries (union), else all.
  const cropOptions = useMemo(() => {
    if (!meta) return [];
    if (!countries.length) return meta.crops;
    const set = new Set<string>();
    countries.forEach((c) => (meta.crops_by_country[c] || []).forEach((cr) => set.add(cr)));
    return Array.from(set).sort();
  }, [meta, countries]);

  async function handlePlot() {
    if (!countries.length || !crops.length) return;
    setPlotting(true);
    setError(null);
    try {
      const res = await fetchHarvestStatSeries({
        countries,
        crops,
        metric,
        season: season || undefined,
      });
      if (!res.series.length) setError("No data for that combination — try different crops or countries.");
      setResult(res);
    } catch {
      setError("Could not fetch the series. Please try again.");
    } finally {
      setPlotting(false);
    }
  }

  function downloadCsv() {
    if (!result) return;
    const rows = [["country", "crop", "year", "value", "metric", "units"]];
    for (const s of result.series) {
      for (const p of s.points) {
        rows.push([s.country, s.crop, String(p.year), String(p.value), result.metric, s.units]);
      }
    }
    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "crop_statistics.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const units = result?.units || "";

  return (
    <main className="max-w-6xl mx-auto px-4 py-16">
      <div className="mb-8">
        <span className="inline-block text-xs font-semibold tracking-wide text-white bg-aic-green rounded-full px-3 py-1 mb-3">
          CROP STATISTICS
        </span>
        <h1 className="text-4xl font-bold text-aic-dark mb-3">Subnational crop yields & production over time</h1>
        <p className="text-aic-muted">
          Openly-licensed harmonized crop statistics from HarvestStat-Africa — area, production and yield by country,
          region, crop and season. Compare several countries or crops as separate lines on one chart.
        </p>
      </div>

      {loadingMeta && <p className="text-aic-muted">Loading crop catalog...</p>}

      {meta && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8 grid gap-6 md:grid-cols-2">
          <div>
            <label className="block text-sm font-semibold text-aic-dark mb-2">Countries</label>
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
              {meta.countries.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCountries((prev) => toggle(prev, c))}
                  className={`text-sm rounded-full px-3 py-1 border ${
                    countries.includes(c)
                      ? "bg-aic-green text-white border-aic-green"
                      : "bg-white text-aic-dark border-slate-300 hover:border-aic-green"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 mt-5">
              <div>
                <label className="block text-xs text-aic-muted mb-1">Metric</label>
                <select className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm" value={metric} onChange={(e) => setMetric(e.target.value)}>
                  {Object.entries(meta.metrics).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-aic-muted mb-1">Season</label>
                <select className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm" value={season} onChange={(e) => setSeason(e.target.value)}>
                  <option value="">Any</option>
                  {meta.seasons.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-aic-dark mb-2">
              Crops <span className="text-aic-muted font-normal">({crops.length} selected)</span>
            </label>
            <div className="h-56 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-1">
              {cropOptions.map((cr) => (
                <label key={cr} className="flex items-start gap-2 text-sm cursor-pointer hover:bg-slate-50 rounded px-1 py-0.5">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={crops.includes(cr)}
                    onChange={() => setCrops((prev) => toggle(prev, cr, 8))}
                  />
                  <span>{cr}</span>
                </label>
              ))}
              {cropOptions.length === 0 && <p className="text-aic-muted text-sm p-2">Select a country to see its crops.</p>}
            </div>
            <button
              type="button"
              onClick={handlePlot}
              disabled={plotting || !countries.length || !crops.length}
              className="btn-primary mt-4 disabled:opacity-50"
            >
              {plotting ? "Plotting..." : "Plot crop statistics"}
            </button>
          </div>
        </section>
      )}

      {error && <p className="text-aic-red mb-6">{error}</p>}

      {result && result.series.length > 0 && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-aic-dark">
              {result.series.length} series{units ? ` · ${units}` : ""}
            </h2>
            <button type="button" onClick={downloadCsv} className="text-sm text-aic-green underline">
              Download CSV
            </button>
          </div>
          <MultiSeriesLineChart series={result.series} yLabel={units} />
        </section>
      )}

      {result && result.series.length > 0 && (
        <AIInsightPanel
          title={`Crop ${result.metric}${units ? ` (${units})` : ""}`}
          metric={result.metric}
          series={result.series.map((s) => ({
            label: s.label, country: s.country, crop: s.crop, units: s.units,
            points: s.points.map((p) => ({ year: p.year, value: p.value })),
          }))}
        />
      )}
    </main>
  );
}
