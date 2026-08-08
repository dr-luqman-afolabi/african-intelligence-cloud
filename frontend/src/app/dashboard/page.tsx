"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchMacroData,
  fetchCountries,
  fetchIndicators,
  type MacroDataResponse,
  type MacroDataPoint,
  type CountryEntry,
  type IndicatorEntry,
  type InsightSeriesInput,
} from "@/lib/api";
import MultiMacroChart, { type ChartSeries } from "@/components/MultiMacroChart";
import PageHeader from "@/components/ui/PageHeader";
import Spinner from "@/components/ui/Spinner";
import AIInsightPanel from "@/components/insights/AIInsightPanel";

const COLORS = ["#0f766e", "#b45309", "#1d4ed8", "#be123c", "#4d7c0f", "#7c3aed", "#c2410c", "#0369a1"];

export default function Dashboard() {
  const [countries, setCountries] = useState<CountryEntry[]>([]);
  const [indicators, setIndicators] = useState<IndicatorEntry[]>([]);
  const [country, setCountry] = useState("NGA");
  const [selectedCodes, setSelectedCodes] = useState<string[]>(["NY.GDP.PCAP.CD"]);
  const [data, setData] = useState<MacroDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCountries().then(setCountries).catch(() => setCountries([]));
    fetchIndicators().then(setIndicators).catch(() => setIndicators([]));
  }, []);

  const loadMacroData = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchMacroData(country)
      .then(setData)
      .catch(() => setError("Macroeconomic data is temporarily unavailable. Please try again."))
      .finally(() => setLoading(false));
  }, [country]);

  useEffect(() => {
    loadMacroData();
  }, [loadMacroData]);

  function toggleIndicator(code: string) {
    setSelectedCodes((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
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

  const insightSeries: InsightSeriesInput[] = useMemo(() => {
    return series
      .filter((s) => s.data.length > 0)
      .map((s) => ({
        label: s.label,
        country: countryName,
        points: s.data.map((d) => ({ year: d.year, value: d.value })),
      }));
  }, [series, countryName]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <PageHeader
        eyebrow="Macro data"
        title="Macro Dashboard"
        description={`Historical macroeconomic, social, and environmental indicators from World Bank Open Data across ${countries.length || 54} African countries.`}
      />

      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Country</label>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="input-field !w-auto min-w-[220px]"
          >
            {countries.map((c) => (
              <option key={c.iso3} value={c.iso3}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="card p-5 mb-8">
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

      {error && (
        <div className="flex flex-wrap items-center justify-between gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadMacroData}
            disabled={loading}
            className="text-sm font-semibold underline underline-offset-2 disabled:opacity-50"
          >
            Try again
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Spinner />
        </div>
      ) : (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-aic-dark mb-1">{countryName}</h2>
          <p className="text-sm text-aic-muted mb-6">{selectedCodes.length} indicator(s) plotted together</p>
          <MultiMacroChart series={series} />

          {insightSeries.length > 0 && (
            <AIInsightPanel title={`${countryName} macro indicators`} metric="macro" series={insightSeries} />
          )}
        </div>
      )}
    </div>
  );
}
