"use client";

import { useEffect, useMemo, useState } from "react";
import MultiSeriesLineChart from "@/components/microdata/MultiSeriesLineChart";
import {
  fetchEparMeta,
  fetchEparSeries,
  type EparMeta,
  type EparSeriesResponse,
} from "@/lib/api";

function toggle(list: string[], value: string, cap = 999): string[] {
  if (list.includes(value)) return list.filter((v) => v !== value);
  if (list.length >= cap) return list;
  return [...list, value];
}

export default function AgIndicatorsPage() {
  const [meta, setMeta] = useState<EparMeta | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [countries, setCountries] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [indicators, setIndicators] = useState<string[]>([]);
  const [gender, setGender] = useState("");
  const [rural, setRural] = useState("");
  const [farmsize, setFarmsize] = useState("");

  const [result, setResult] = useState<EparSeriesResponse | null>(null);
  const [plotting, setPlotting] = useState(false);

  useEffect(() => {
    fetchEparMeta()
      .then((m) => {
        setMeta(m);
        if (m.countries.length) setCountries(m.countries.slice(0, 3));
        if (m.categories.length) setCategory(m.categories[0]);
        if (!m.loaded) setError("The indicator dataset is still loading on the server — try again in a moment.");
      })
      .catch(() => setError("Could not load the indicator catalog."))
      .finally(() => setLoadingMeta(false));
  }, []);

  const indicatorOptions = useMemo(
    () => (meta && category ? meta.indicators_by_category[category] || [] : []),
    [meta, category],
  );

  async function handlePlot() {
    if (!countries.length || !indicators.length) return;
    setPlotting(true);
    setError(null);
    try {
      const res = await fetchEparSeries({
        countries,
        indicators,
        gender: gender || undefined,
        rural: rural || undefined,
        farmsize: farmsize || undefined,
      });
      if (!res.series.length) {
        setError("No estimates for that combination — try clearing the disaggregation filters.");
      }
      setResult(res);
    } catch {
      setError("Could not fetch the series. Please try again.");
    } finally {
      setPlotting(false);
    }
  }

  function downloadCsv() {
    if (!result) return;
    const rows = [["country", "indicator", "wave", "year", "value", "n", "units"]];
    for (const s of result.series) {
      for (const p of s.points) {
        rows.push([s.country, s.indicator, p.wave, p.year, String(p.value), p.n == null ? "" : String(p.n), s.units]);
      }
    }
    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "ag_indicators.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const units = result?.series[0]?.units || "";

  return (
    <main className="max-w-6xl mx-auto px-4 py-16">
      <div className="mb-8">
        <span className="inline-block text-xs font-semibold tracking-wide text-white bg-aic-green rounded-full px-3 py-1 mb-3">
          AG DEVELOPMENT INDICATORS
        </span>
        <h1 className="text-4xl font-bold text-aic-dark mb-3">Compare indicators across countries & waves</h1>
        <p className="text-aic-muted">
          Openly-licensed LSMS-ISA indicator estimates from EPAR — 5 countries, 27 survey waves, 150 indicators.
          Pick one or more countries and indicators to plot them as separate lines on one chart.
        </p>
      </div>

      {loadingMeta && <p className="text-aic-muted">Loading indicator catalog...</p>}

      {meta && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8 grid gap-6 md:grid-cols-2">
          <div>
            <label className="block text-sm font-semibold text-aic-dark mb-2">Countries</label>
            <div className="flex flex-wrap gap-2">
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

            <label className="block text-sm font-semibold text-aic-dark mt-5 mb-1">Indicator category</label>
            <select
              className="w-full border border-slate-300 rounded-lg px-3 py-2"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setIndicators([]);
              }}
            >
              {meta.categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            <div className="grid grid-cols-2 gap-3 mt-5">
              <div>
                <label className="block text-xs text-aic-muted mb-1">Gender</label>
                <select className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm" value={gender} onChange={(e) => setGender(e.target.value)}>
                  <option value="">Any</option>
                  {meta.gender.map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-aic-muted mb-1">Population</label>
                <select className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm" value={rural} onChange={(e) => setRural(e.target.value)}>
                  <option value="">Any</option>
                  {meta.rural.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-aic-dark mb-2">
              Indicators <span className="text-aic-muted font-normal">({indicators.length} selected)</span>
            </label>
            <div className="h-56 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-1">
              {indicatorOptions.map((ind) => (
                <label key={ind} className="flex items-start gap-2 text-sm cursor-pointer hover:bg-slate-50 rounded px-1 py-0.5">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={indicators.includes(ind)}
                    onChange={() => setIndicators((prev) => toggle(prev, ind, 8))}
                  />
                  <span>{ind}</span>
                </label>
              ))}
              {indicatorOptions.length === 0 && <p className="text-aic-muted text-sm p-2">No indicators in this category.</p>}
            </div>
            <button
              type="button"
              onClick={handlePlot}
              disabled={plotting || !countries.length || !indicators.length}
              className="btn-primary mt-4 disabled:opacity-50"
            >
              {plotting ? "Plotting..." : "Plot indicators"}
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
    </main>
  );
}
