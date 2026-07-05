"use client";

import { useEffect, useMemo, useState } from "react";
import {
  fetchMacroData,
  fetchCountries,
  fetchIndicators,
  fetchMacroInterpretation,
  type MacroDataResponse,
  type MacroDataPoint,
  type CountryEntry,
  type IndicatorEntry,
} from "@/lib/api";
import MultiMacroChart, { type ChartSeries } from "@/components/MultiMacroChart";

const COLORS = ["#0f766e", "#b45309", "#1d4ed8", "#be123c", "#4d7c0f", "#7c3aed", "#c2410c", "#0369a1"];

export default function Dashboard() {
  const [countries, setCountries] = useState<CountryEntry[]>([]);
  const [indicators, setIndicators] = useState<IndicatorEntry[]>([]);
  const [country, setCountry] = useState("NGA");
  const [selectedCodes, setSelectedCodes] = useState<string[]>(["NY.GDP.PCAP.CD"]);
  const [data, setData] = useState<MacroDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [interpreting, setInterpreting] = useState(false);

  useEffect(() => {
    fetchCountries().then(setCountries).catch(() => setCountries([]));
    fetchIndicators().then(setIndicators).catch(() => setIndicators([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setInterpretation(null);
    fetchMacroData(country)
      .then(setData)
      .catch(() => setError("Failed to load data. Make sure the backend is running."))
      .finally(() => setLoading(false));
  }, [country]);

  function toggleIndicator(code: string) {
    setSelectedCodes((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
    setInterpretation(null);
  }

  const grouped = useMemo(() => {
    const map: Record<string, IndicatorEntry[]> = {};
    indicators.forEach((ind) => {
      const key = ind.category || "Other";
      if (!map[key]) map[key] = [];
      map[key].push(ind);
    });
    return map;
  }, [indicators]);

  const series: ChartSeries[] = useMemo(() => {
    return selectedCodes.map((code, i) => {
      const meta = indicators.find((ind) => ind.code === code);
      const points = (data?.data ?? [])
        .filter((d: MacroDataPoint) => d.indicator_code === code)
        .sort((a: MacroDataPoint, b: MacroDataPoint) => a.year - b.year)
        .map((d: MacroDataPoint) => ({ year: d.year, value: d.value }));
      return {
        code,
        label: meta?.name || code,
        color: COLORS[i % COLORS.length],
        data: points,
      };
    });
  }, [selectedCodes, data, indicators]);

  const countryName = data?.country_name ?? country;

  async function handleInterpret() {
    if (selectedCodes.length === 0) return;
    setInterpreting(true);
    try {
      const result = await fetchMacroInterpretation(country, selectedCodes);
      setInterpretation(result.narrative);
    } catch {
      setInterpretation("Could not generate an interpretation right now. Try again after the data has synced.");
    } finally {
      setInterpreting(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-aic-dark mb-2">Macro Dashboard</h1>
      <p className="text-aic-muted mb-8">
        Historical macroeconomic, social, and environmental indicators from World Bank Open Data across {countries.length || 54}+ African countries.
      </p>

      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Country</label>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-aic-green"
          >
            {countries.map((c) => (
              <option key={c.iso3} value={c.iso3}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 mb-8">
        <h2 className="text-sm font-semibold text-aic-dark mb-3">
          Select indicators to combine on one chart ({selectedCodes.length} selected)
        </h2>
        <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
          {Object.entries(grouped).map(([category, inds]) => (
            <div key={category}>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">{category}</p>
              <div className="flex flex-wrap gap-2">
                {inds.map((ind) => (
                  <button
                    key={ind.code}
                    onClick={() => toggleIndicator(ind.code)}
                    className={selectedCodes.includes(ind.code) ? "px-3 py-1.5 rounded-full text-xs font-medium bg-aic-dark text-white transition" : "px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition"}
                  >
                    {ind.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">{error}</div>}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-4 border-aic-green border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-semibold text-aic-dark mb-1">{countryName}</h2>
          <p className="text-sm text-aic-muted mb-6">{selectedCodes.length} indicator(s) plotted together</p>
          <MultiMacroChart series={series} />

          <div className="mt-8 border-t border-slate-100 pt-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-aic-dark">AI Interpretation</h3>
              <button
                onClick={handleInterpret}
                disabled={interpreting || selectedCodes.length === 0}
                className="px-4 py-1.5 rounded-full text-sm font-medium bg-aic-green text-white hover:opacity-90 transition disabled:opacity-50"
              >
                {interpreting ? "Analyzing..." : "Generate Interpretation"}
              </button>
            </div>
            {interpretation ? (
              <p className="text-sm text-slate-700 leading-relaxed">{interpretation}</p>
            ) : (
              <p className="text-sm text-aic-muted">
                Click Generate Interpretation for an automated, data-driven narrative analysis of the selected indicators.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
