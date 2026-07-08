"use client";
import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { fetchSDGGoals, fetchSDGData, fetchCountries, SDGGoal, CountryEntry } from "@/lib/api";

const SDG_COLORS = [
  "#e5243b", "#dda63a", "#4c9f38", "#c5192d", "#ff3a21",
  "#26bde2", "#fcc30b", "#a21942", "#fd6925", "#dd1367",
  "#fd9d24", "#bf8b2e", "#3f7e44", "#0a97d9", "#56c02b",
  "#00689d", "#19486a",
];

const REGION_COLORS = ["#0f766e", "#b45309", "#1d4ed8", "#be123c", "#7c3aed", "#0369a1"];

interface SDGSeriesPoint {
  country: string;
  year: number;
  value: number;
}

interface CountryBreakdownEntry {
  country_iso3: string;
  country_name: string;
  region: string | null;
  year: number;
  value: number;
}

interface SDGSeriesEntry {
  indicator_code: string;
  indicator_name: string;
  unit: string;
  data: SDGSeriesPoint[];
  country_breakdown?: CountryBreakdownEntry[];
}

const CLIMATE_KEYWORDS = ["rainfall", "precipitation", "temperature"];
const AGRI_KEYWORDS = ["agricultur", "cereal", "yield", "crop"];

function isClimateOrAgri(name: string): boolean {
  const n = name.toLowerCase();
  return CLIMATE_KEYWORDS.some((k) => n.includes(k)) || AGRI_KEYWORDS.some((k) => n.includes(k));
}

const numFmt = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 });

function SDGIndicatorCard({
  series,
  color,
  isAggregate,
}: {
  series: SDGSeriesEntry;
  color: string;
  isAggregate: boolean;
}) {
  const [view, setView] = useState<"trend" | "countries">("trend");
  const breakdown = useMemo(() => series.country_breakdown ?? [], [series.country_breakdown]);

  // Stable color per region so the ranking doubles as a regional comparison.
  const regionColor = useMemo(() => {
    const regions = Array.from(new Set(breakdown.map((b) => b.region || "Other")));
    const map: Record<string, string> = {};
    regions.forEach((r, i) => {
      map[r] = REGION_COLORS[i % REGION_COLORS.length];
    });
    return map;
  }, [breakdown]);

  const topCountries = breakdown.slice(0, 15);

  return (
    <div
      className={`bg-white rounded-xl border shadow-sm p-4 space-y-2 ${
        isClimateOrAgri(series.indicator_name) ? "border-emerald-300 ring-1 ring-emerald-100" : "border-slate-200"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-slate-700">{series.indicator_name}</p>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">{series.unit}</span>
          {breakdown.length > 0 && (
            <div className="inline-flex rounded-full bg-slate-100 p-0.5">
              <button
                onClick={() => setView("trend")}
                className={`px-2 py-0.5 rounded-full text-[11px] font-medium transition ${
                  view === "trend" ? "bg-slate-900 text-white" : "text-slate-500"
                }`}
              >
                Trend
              </button>
              <button
                onClick={() => setView("countries")}
                className={`px-2 py-0.5 rounded-full text-[11px] font-medium transition ${
                  view === "countries" ? "bg-slate-900 text-white" : "text-slate-500"
                }`}
              >
                Countries
              </button>
            </div>
          )}
        </div>
      </div>
      {isClimateOrAgri(series.indicator_name) && (
        <span className="inline-block text-[10px] font-semibold uppercase tracking-wide text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
          Environment / Agriculture
        </span>
      )}

      {view === "trend" ? (
        <>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={series.data.map((d) => ({ year: d.year, value: d.value }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} tickFormatter={(v: number) => numFmt.format(v)} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
              />
              <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          {isAggregate && (
            <p className="text-[11px] text-slate-400">
              Unweighted average across all African countries with data — switch to
              &quot;Countries&quot; to see individual country values.
            </p>
          )}
        </>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={Math.max(220, topCountries.length * 22)}>
            <BarChart data={topCountries} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} tickFormatter={(v: number) => numFmt.format(v)} />
              <YAxis
                type="category"
                dataKey="country_name"
                width={110}
                tick={{ fontSize: 11, fill: "#475569" }}
                interval={0}
              />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
                formatter={(value: number, _name, item) => {
                  const entry = item?.payload as CountryBreakdownEntry | undefined;
                  return [
                    `${numFmt.format(value)} (${entry?.year ?? "?"})`,
                    entry?.region ?? "value",
                  ];
                }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {topCountries.map((entry) => (
                  <Cell key={entry.country_iso3} fill={regionColor[entry.region || "Other"]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {Object.entries(regionColor).map(([region, c]) => (
              <span key={region} className="flex items-center gap-1 text-[11px] text-slate-500">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: c }} />
                {region}
              </span>
            ))}
          </div>
          <p className="text-[11px] text-slate-400">
            Top {topCountries.length} of {breakdown.length} countries, latest available year per country.
          </p>
        </>
      )}
    </div>
  );
}

export default function SDGPage() {
  const [goals, setGoals] = useState<SDGGoal[]>([]);
  const [countries, setCountries] = useState<CountryEntry[]>([]);
  const [selectedGoal, setSelectedGoal] = useState<number>(1);
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [rawSeries, setRawSeries] = useState<SDGSeriesEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSDGGoals()
      .then(setGoals)
      .catch(() => setError("Could not load SDG goals."))
      .finally(() => setLoading(false));
    fetchCountries()
      .then(setCountries)
      .catch(() => setCountries([]));
  }, []);

  useEffect(() => {
    if (!selectedGoal) return;
    setDataLoading(true);
    fetchSDGData(selectedGoal, selectedCountry || undefined)
      .then((res) => {
        setRawSeries((res.series ?? []) as SDGSeriesEntry[]);
      })
      .catch(() => setRawSeries([]))
      .finally(() => setDataLoading(false));
  }, [selectedGoal, selectedCountry]);

  const currentGoal = goals.find((g) => g.goal_number === selectedGoal);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-white border-r border-slate-200 overflow-y-auto">
        <div className="px-4 py-4 border-b border-slate-100">
          <h2 className="font-bold text-slate-800 text-sm">SDG Goals</h2>
          <p className="text-xs text-slate-400">Sustainable Development Goals</p>
        </div>
        <nav className="py-2">
          {loading
            ? Array.from({ length: 17 }).map((_, i) => (
                <div
                  key={i}
                  className="mx-3 my-1 h-8 rounded-lg bg-slate-100 animate-pulse"
                />
              ))
            : goals.map((g) => (
                <button
                  key={g.goal_number}
                  onClick={() => setSelectedGoal(g.goal_number)}
                  className={`w-full text-left px-4 py-2.5 flex items-center gap-3 text-sm transition ${
                    selectedGoal === g.goal_number
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <span
                    className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold shrink-0"
                    style={{ backgroundColor: SDG_COLORS[(g.goal_number - 1) % 17] }}
                  >
                    {g.goal_number}
                  </span>
                  <span className="truncate text-xs">{g.title}</span>
                </button>
              ))}
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {currentGoal && (
          <>
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-start gap-4">
                <span
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-xl font-bold shrink-0"
                  style={{ backgroundColor: SDG_COLORS[(currentGoal.goal_number - 1) % 17] }}
                >
                  {currentGoal.goal_number}
                </span>
                <div>
                  <h1 className="text-xl font-bold text-slate-800">{currentGoal.title}</h1>
                  <p className="text-sm text-slate-500 mt-0.5">{currentGoal.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs font-medium text-slate-500">Country</label>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="border border-slate-200 rounded-lg text-sm px-3 py-2 bg-white"
                >
                  <option value="">All countries (Africa average)</option>
                  {countries.map((c) => (
                    <option key={c.iso3} value={c.iso3}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Indicator list */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-700">
                  Tracked Indicators ({currentGoal.indicators.length})
                </p>
              </div>
              {currentGoal.indicators.length === 0 ? (
                <p className="px-4 py-6 text-sm text-slate-400 text-center">
                  No indicators mapped to this goal in the current dataset.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-slate-500 uppercase tracking-wide border-b border-slate-100">
                      <th className="text-left px-4 py-2">Indicator</th>
                      <th className="text-left px-4 py-2">Code</th>
                      <th className="text-right px-4 py-2">Countries</th>
                      <th className="text-right px-4 py-2">Latest Year</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentGoal.indicators.map((ind, i) => (
                      <tr
                        key={i}
                        className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60"
                      >
                        <td className="px-4 py-2.5 font-medium text-slate-700">
                          {ind.indicator_name}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs text-slate-500">
                          {ind.indicator_code}
                        </td>
                        <td className="px-4 py-2.5 text-right text-slate-600">
                          {ind.available_countries}
                        </td>
                        <td className="px-4 py-2.5 text-right text-slate-600">
                          {ind.latest_year ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {(currentGoal.goal_number === 13 || currentGoal.goal_number === 2 || currentGoal.goal_number === 15) && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-amber-800 text-sm space-y-1">
                <p className="font-semibold">Environmental &amp; agricultural data note</p>
                <p>
                  Rainfall (average precipitation) and agricultural productivity (cereal yield) below are
                  real World Bank series. A standalone global temperature time-series is not part of the
                  standard World Bank development indicators, so it is intentionally not shown here to
                  avoid fabricating data — rainfall is provided as the available climate proxy.
                </p>
              </div>
            )}

            {/* Individual series charts */}
            <div className="space-y-3">
              <p className="text-sm font-semibold text-slate-700">Individual Indicator Series</p>
              {dataLoading ? (
                <div className="h-64 flex items-center justify-center text-slate-400 text-sm bg-white rounded-xl border border-slate-200">
                  Loading chart data…
                </div>
              ) : rawSeries.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-slate-400 text-sm bg-white rounded-xl border border-slate-200">
                  No time-series data available for this goal{selectedCountry ? " and country" : ""}.
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {rawSeries.map((s, idx) => (
                    <SDGIndicatorCard
                      key={s.indicator_code}
                      series={s}
                      color={SDG_COLORS[idx % 17]}
                      isAggregate={!selectedCountry}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
