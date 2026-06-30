"use client";

import { useEffect, useState } from "react";
import { fetchMacroData, type MacroDataResponse, type MacroDataPoint } from "@/lib/api";
import MacroChart from "@/components/MacroChart";

const COUNTRIES = [
  { iso3: "NGA", name: "Nigeria" },
  { iso3: "RWA", name: "Rwanda" },
  { iso3: "ZAF", name: "South Africa" },
  { iso3: "GHA", name: "Ghana" },
  { iso3: "KEN", name: "Kenya" },
  { iso3: "ETH", name: "Ethiopia" },
];

const INDICATORS = [
  { code: "NY.GDP.PCAP.CD", label: "GDP per Capita (USD)" },
  { code: "NY.GDP.MKTP.KD.ZG", label: "GDP Growth Rate (%)" },
  { code: "FP.CPI.TOTL.ZG", label: "Inflation Rate (%)" },
  { code: "SL.UEM.TOTL.ZS", label: "Unemployment Rate (%)" },
  { code: "GC.DOD.TOTL.GD.ZS", label: "Government Debt (% GDP)" },
];

export default function Dashboard() {
  const [country, setCountry] = useState("NGA");
  const [indicator, setIndicator] = useState("NY.GDP.PCAP.CD");
  const [data, setData] = useState<MacroDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchMacroData(country)
      .then(setData)
      .catch(() => setError("Failed to load data. Make sure the backend is running."))
      .finally(() => setLoading(false));
  }, [country]);

  const chartData = (data?.data ?? [])
    .filter((d: MacroDataPoint) => d.indicator_code === indicator)
    .sort((a: MacroDataPoint, b: MacroDataPoint) => a.year - b.year)
    .map((d: MacroDataPoint) => ({ year: d.year, value: d.value }));

  const selectedIndicator = INDICATORS.find((i) => i.code === indicator);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-aic-dark mb-2">Macro Dashboard</h1>
      <p className="text-aic-muted mb-8">Historical macroeconomic indicators from World Bank</p>

      <div className="flex flex-wrap gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Country</label>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-aic-green"
          >
            {COUNTRIES.map((c) => (
              <option key={c.iso3} value={c.iso3}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Indicator</label>
          <select
            value={indicator}
            onChange={(e) => setIndicator(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-aic-green"
          >
            {INDICATORS.map((i) => (
              <option key={i.code} value={i.code}>{i.label}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-4 border-aic-green border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-semibold text-aic-dark mb-1">
            {data?.country_name ?? country} — {selectedIndicator?.label}
          </h2>
          <p className="text-sm text-aic-muted mb-6">{chartData.length} data points</p>
          {chartData.length > 0 ? (
            <MacroChart data={chartData} label={selectedIndicator?.label ?? indicator} />
          ) : (
            <div className="text-center text-aic-muted py-16">
              No data available. Try running a sync first.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
