"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchMicrodataDatasets,
  fetchMicrodataVariables,
  runPovertyAnalysis,
  type MicrodataDataset,
  type MicrodataVariable,
} from "@/lib/api";
import VariableSelect from "@/components/microdata/VariableSelect";
import { GroupBarChart, GroupRankingTable, type GroupPovertyRow } from "@/components/microdata/PovertyCharts";
import { AFRICAN_COUNTRIES, ADMIN_LEVELS, CHART_TYPES } from "@/lib/africaCountries";
import { downloadCSV, exportChartAsPng } from "@/lib/exportUtils";

type ChartType = (typeof CHART_TYPES)[number]["value"];

interface PovertySummary {
  headcount?: number;
  poverty_gap?: number;
  squared_poverty_gap?: number;
  gini?: number;
  n_obs?: number;
}

export default function MicrodataDashboardPanel() {
  const router = useRouter();
  const chartRef = useRef<HTMLDivElement>(null);

  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [variables, setVariables] = useState<MicrodataVariable[]>([]);

  const [countryIso3, setCountryIso3] = useState("RWA");
  const [adminLevel, setAdminLevel] = useState("ADM2");
  const [chartType, setChartType] = useState<ChartType>("bar");

  const [welfareVar, setWelfareVar] = useState("");
  const [weightVar, setWeightVar] = useState("");
  const [groupBy, setGroupBy] = useState("");
  const [povertyLine, setPovertyLine] = useState(100);

  const [summary, setSummary] = useState<PovertySummary | null>(null);
  const [rows, setRows] = useState<GroupPovertyRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMicrodataDatasets()
      .then((res) => {
        setDatasets(res.items);
        if (res.items.length > 0) {
          setDatasetId(res.items[0].id);
          if (res.items[0].country_iso3) setCountryIso3(res.items[0].country_iso3);
        }
      })
      .catch(() => setError("Log in to load your microdata datasets."));
  }, []);

  useEffect(() => {
    if (!datasetId) return;
    fetchMicrodataVariables(datasetId).then(setVariables).catch(() => setVariables([]));
  }, [datasetId]);

  async function runAnalysis() {
    if (!datasetId || !welfareVar) {
      setError("Select a dataset and welfare variable first.");
      return;
    }
    if (chartType === "map") {
      if (!groupBy) {
        setError("Select a geography variable (Group by) to draw a map.");
        return;
      }
      const params = new URLSearchParams({
        dataset_id: datasetId,
        geo_variable: groupBy,
        welfare_variable: welfareVar,
        poverty_line: String(povertyLine),
      });
      if (weightVar) params.set("weight_variable", weightVar);
      router.push(`/microdata/spatial?${params.toString()}`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await runPovertyAnalysis({
        dataset_id: datasetId,
        welfare_variable: welfareVar,
        poverty_line: povertyLine,
        weight_variable: weightVar || undefined,
        group_by: groupBy ? [groupBy] : undefined,
      });
      if (res.status === "failed") {
        setError(res.error_message || "Analysis failed. Check the selected variables.");
        return;
      }
      setSummary((res.summary_stats || {}) as PovertySummary);
      const tables = (res.tables || {}) as Record<string, unknown>;
      setRows(groupBy ? ((tables[groupBy] || []) as GroupPovertyRow[]) : []);
    } catch {
      setError("Analysis failed. Check the selected variables.");
    } finally {
      setLoading(false);
    }
  }

  function resetFilters() {
    setWelfareVar("");
    setWeightVar("");
    setGroupBy("");
    setPovertyLine(100);
    setChartType("bar");
    setSummary(null);
    setRows([]);
    setError(null);
  }

  const fmtPct = (v: number | undefined) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—");

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Country</label>
          <select value={countryIso3} onChange={(e) => setCountryIso3(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white w-full">
            {AFRICAN_COUNTRIES.map((c) => (
              <option key={c.iso3} value={c.iso3}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Dataset</label>
          <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white w-full">
            <option value="">Select…</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <VariableSelect label="Welfare variable" variables={variables} value={welfareVar} onChange={setWelfareVar} />
        <VariableSelect label="Weight variable" variables={variables} value={weightVar} onChange={setWeightVar} allowNone />
        <VariableSelect label="Group by / geography" variables={variables} value={groupBy} onChange={setGroupBy} allowNone />

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Poverty line</label>
          <input type="number" value={povertyLine} onChange={(e) => setPovertyLine(Number(e.target.value))} className="border border-slate-200 rounded-lg px-3 py-2 text-sm w-full" />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Admin level</label>
          <select value={adminLevel} onChange={(e) => setAdminLevel(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white w-full">
            {ADMIN_LEVELS.map((a) => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Chart type</label>
          <select value={chartType} onChange={(e) => setChartType(e.target.value as ChartType)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white w-full">
            {CHART_TYPES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-end gap-2 col-span-2 md:col-span-4">
          <button onClick={runAnalysis} disabled={loading} className="px-4 py-2 bg-aic-green text-white text-sm font-semibold rounded-lg disabled:opacity-50">
            {loading ? "Running…" : "Run Analysis"}
          </button>
          <button onClick={resetFilters} className="px-4 py-2 bg-white border border-slate-200 text-sm font-medium rounded-lg hover:border-slate-400">
            Reset Filters
          </button>
          {rows.length > 0 && (
            <>
              <button
                onClick={() => downloadCSV(rows, "poverty-by-group.csv")}
                className="px-4 py-2 bg-white border border-slate-200 text-sm font-medium rounded-lg hover:border-slate-400"
              >
                Export CSV
              </button>
              <button
                onClick={() => exportChartAsPng(chartRef.current, "poverty-chart.png")}
                className="px-4 py-2 bg-white border border-slate-200 text-sm font-medium rounded-lg hover:border-slate-400"
              >
                Export PNG
              </button>
            </>
          )}
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm mb-4">{error}</div>}

      {summary && (
        <div className="grid md:grid-cols-2 gap-6 pt-2">
          <div ref={chartRef}>
            <p className="text-xs text-slate-500 mb-2">
              Headcount {fmtPct(summary.headcount)} · Poverty gap {fmtPct(summary.poverty_gap)} · Gini{" "}
              {typeof summary.gini === "number" ? summary.gini.toFixed(3) : "—"} · n ={" "}
              {summary.n_obs ?? "—"}
            </p>
            <GroupBarChart
              data={rows}
              dataKey="headcount"
              label="Headcount"
              chartType={chartType === "map" ? "bar" : chartType}
            />
          </div>
          <GroupRankingTable data={rows} />
        </div>
      )}
    </div>
  );
}
