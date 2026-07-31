"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchConsumptionCatalog,
  fetchEparPackages,
  fetchMicrodataDatasets,
  fetchMicrodataVariables,
  runPovertyAnalysis,
  type ConsumptionDataset,
  type EparPackage,
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
  const [eparPackages, setEparPackages] = useState<EparPackage[]>([]);
  const [consumptionDatasets, setConsumptionDatasets] = useState<ConsumptionDataset[]>([]);
  const [datasetSelection, setDatasetSelection] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [variables, setVariables] = useState<MicrodataVariable[]>([]);
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [sourceCatalogsLoading, setSourceCatalogsLoading] = useState(true);
  const [authenticationRequired, setAuthenticationRequired] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);

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
        setAuthenticationRequired(false);
        if (res.items.length > 0) {
          setDatasetSelection(`dataset:${res.items[0].id}`);
          setDatasetId(res.items[0].id);
          if (res.items[0].country_iso3) setCountryIso3(res.items[0].country_iso3);
        }
      })
      .catch(() => setAuthenticationRequired(true))
      .finally(() => setDatasetsLoading(false));

    Promise.all([fetchEparPackages(), fetchConsumptionCatalog()])
      .then(([epar, consumption]) => {
        setEparPackages(epar.packages);
        setConsumptionDatasets(consumption.datasets);
        setCatalogError(null);
      })
      .catch(() => setCatalogError("The integrated source catalogs could not be loaded. Please refresh the page."))
      .finally(() => setSourceCatalogsLoading(false));
  }, []);

  useEffect(() => {
    if (!datasetId) {
      setVariables([]);
      return;
    }
    fetchMicrodataVariables(datasetId).then(setVariables).catch(() => setVariables([]));
  }, [datasetId]);

  function selectDataset(value: string) {
    setDatasetSelection(value);
    setWelfareVar("");
    setWeightVar("");
    setGroupBy("");
    setSummary(null);
    setRows([]);
    setError(null);

    if (value.startsWith("dataset:")) {
      const id = value.slice("dataset:".length);
      const selected = datasets.find((item) => item.id === id);
      setDatasetId(id);
      if (selected?.country_iso3) setCountryIso3(selected.country_iso3);
      return;
    }

    setDatasetId("");
    if (value.startsWith("epar:")) {
      const selected = eparPackages.find((item) => item.id === value.slice("epar:".length));
      if (selected?.country_iso3) setCountryIso3(selected.country_iso3);
    } else if (value.startsWith("consumption:")) {
      const selected = consumptionDatasets.find(
        (item) => item.id === value.slice("consumption:".length),
      );
      if (selected?.country_iso3) setCountryIso3(selected.country_iso3);
    }
  }

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
        country_iso3: countryIso3,
        admin_level: adminLevel,
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
  const selectedEpar = datasetSelection.startsWith("epar:")
    ? eparPackages.find((item) => item.id === datasetSelection.slice("epar:".length))
    : undefined;
  const selectedConsumption = datasetSelection.startsWith("consumption:")
    ? consumptionDatasets.find(
        (item) => item.id === datasetSelection.slice("consumption:".length),
      )
    : undefined;
  const selectedSource = selectedEpar || selectedConsumption;
  const selectorLoading = datasetsLoading || sourceCatalogsLoading;

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
          <select
            value={datasetSelection}
            onChange={(e) => selectDataset(e.target.value)}
            disabled={selectorLoading}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white w-full disabled:bg-slate-50"
          >
            <option value="">{selectorLoading ? "Loading datasets…" : "Select a dataset…"}</option>
            {datasets.length > 0 && (
              <optgroup label="Analysis-ready datasets">
                {datasets.map((d) => (
                  <option key={d.id} value={`dataset:${d.id}`}>
                    {d.name}{d.country_iso3 ? ` — ${d.country_iso3}` : ""}{d.year ? ` (${d.year})` : ""}
                  </option>
                ))}
              </optgroup>
            )}
            {eparPackages.length > 0 && (
              <optgroup label="EPAR LSMS source packages">
                {eparPackages.map((item) => (
                  <option key={item.id} value={`epar:${item.id}`}>
                    {item.country_iso3} — {item.programme} {item.wave} ({item.years})
                  </option>
                ))}
              </optgroup>
            )}
            {consumptionDatasets.length > 0 && (
              <optgroup label="Household consumption source datasets">
                {consumptionDatasets.map((item) => (
                  <option key={item.id} value={`consumption:${item.id}`}>
                    {item.country} — {item.survey} {item.wave} ({item.years})
                  </option>
                ))}
              </optgroup>
            )}
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
          <button onClick={runAnalysis} disabled={loading || !datasetId || !welfareVar} className="px-4 py-2 bg-aic-green text-white text-sm font-semibold rounded-lg disabled:opacity-50">
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

      {authenticationRequired && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-lg p-3 text-sm mb-4">
          Sign in to see datasets already imported into the analysis database. The integrated source
          catalogs remain available in the selector below.
        </div>
      )}

      {!datasetsLoading && !authenticationRequired && datasets.length === 0 && (
        <div className="bg-slate-50 border border-slate-200 text-slate-700 rounded-lg p-3 text-sm mb-4">
          No analysis-ready dataset has been imported yet. Select an integrated source below, then
          download and upload it before running an analysis.
        </div>
      )}

      {selectedSource && (
        <div className="bg-blue-50 border border-blue-200 text-blue-900 rounded-lg p-3 text-sm mb-4">
          <p className="font-medium">Source dataset selected: {selectedSource.file_name}</p>
          <p className="mt-1">
            This catalog entry must be downloaded and imported before its variables can be analyzed.
          </p>
          <div className="flex flex-wrap gap-3 mt-2">
            <a
              href={selectedSource.download_url}
              target="_blank"
              rel="noreferrer"
              className="font-semibold underline"
            >
              Download source file
            </a>
            <a
              href={selectedEpar ? "/microdata/indicators" : "/consumption"}
              className="font-semibold underline"
            >
              Open full catalog
            </a>
          </div>
        </div>
      )}

      {catalogError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm mb-4">
          {catalogError}
        </div>
      )}

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
