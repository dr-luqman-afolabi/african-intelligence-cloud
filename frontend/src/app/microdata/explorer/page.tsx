"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import dynamic from "next/dynamic";
import {
  fetchMicrodataDatasets,
  fetchMicrodataVariables,
  createExplorerSession,
  updateExplorerSession,
  listExplorerSessions,
  runExplorerSession,
  type MicrodataDataset,
  type MicrodataVariable,
  type ExplorerLayer,
  type ExplorerFilter,
  type ExplorerSession,
  type ExplorerSessionState,
  type AnalysisResultResponse,
} from "@/lib/api";
import DatasetGallery from "@/components/microdata/DatasetGallery";
import AIPolicyBriefPanel from "@/components/microdata/AIPolicyBriefPanel";

const ChoroplethMap = dynamic(() => import("@/components/microdata/ChoroplethMap"), {
  ssr: false,
  loading: () => <div className="h-64 flex items-center justify-center text-aic-muted text-sm">Loading map…</div>,
});

const LAYERS: { id: ExplorerLayer; label: string; valueField: string; valueLabel: string }[] = [
  { id: "poverty", label: "Poverty", valueField: "poverty_headcount", valueLabel: "Poverty headcount" },
  { id: "agriculture", label: "Agriculture", valueField: "crop_yield", valueLabel: "Crop yield" },
  { id: "diversification", label: "Diversification", valueField: "crop_simpson_index", valueLabel: "Crop Simpson index" },
];

const FILTER_OPS = ["eq", "ne", "in", "not_in", "gt", "gte", "lt", "lte", "between", "contains"];
const ADMIN_LEVELS = ["ADM0", "ADM1", "ADM2", "ADM3"];

export default function SpatialExplorerPage() {
  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [dataset, setDataset] = useState<MicrodataDataset | null>(null);
  const [variables, setVariables] = useState<MicrodataVariable[]>([]);

  const [layer, setLayer] = useState<ExplorerLayer>("poverty");
  const [geoVariable, setGeoVariable] = useState("");
  const [weightVariable, setWeightVariable] = useState("");
  const [welfareVariable, setWelfareVariable] = useState("");
  const [povertyLine, setPovertyLine] = useState<number>(0);
  const [cropColumns, setCropColumns] = useState<string[]>([]);
  const [countryIso3, setCountryIso3] = useState("");
  const [adminLevel, setAdminLevel] = useState("");
  const [filters, setFilters] = useState<ExplorerFilter[]>([]);

  const [sessions, setSessions] = useState<ExplorerSession[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionName, setSessionName] = useState("Untitled exploration");

  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const varNames = useMemo(() => variables.map((v) => v.variable_name), [variables]);

  const loadSessions = useCallback(() => {
    listExplorerSessions().then(setSessions).catch(() => {});
  }, []);

  useEffect(() => {
    setDatasetsLoading(true);
    fetchMicrodataDatasets(0, 100)
      .then((res) => setDatasets(res.items))
      .catch(() => setError("Could not load datasets. Please sign in and try again."))
      .finally(() => setDatasetsLoading(false));
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!dataset) return;
    fetchMicrodataVariables(dataset.id).then(setVariables).catch(() => setVariables([]));
    setCountryIso3(dataset.country_iso3 || "");
  }, [dataset]);

  const buildState = useCallback((): ExplorerSessionState => {
    const state: ExplorerSessionState = {
      geo_variable: geoVariable || undefined,
      weight_variable: weightVariable || undefined,
      filters: filters.length ? filters : undefined,
    };
    if (layer === "poverty") {
      state.welfare_variable = welfareVariable || undefined;
      state.poverty_line = povertyLine || undefined;
    } else if (layer === "diversification") {
      state.crop_columns = cropColumns.length ? cropColumns : undefined;
    }
    return state;
  }, [geoVariable, weightVariable, filters, layer, welfareVariable, povertyLine, cropColumns]);

  async function ensureSession(): Promise<string> {
    const payload = {
      name: sessionName,
      dataset_id: dataset?.id ?? null,
      country_iso3: countryIso3 || null,
      admin_level: adminLevel || null,
      active_layer: layer,
      state: buildState(),
    };
    if (sessionId) {
      await updateExplorerSession(sessionId, payload);
      return sessionId;
    }
    const created = await createExplorerSession(payload);
    setSessionId(created.id);
    loadSessions();
    return created.id;
  }

  async function handleRun() {
    setError(null);
    setNotice(null);
    if (!dataset) return setError("Select a dataset first.");
    if (!geoVariable) return setError("Choose a geography variable (the admin unit column).");
    if (layer === "poverty" && (!welfareVariable || !povertyLine)) {
      return setError("Poverty layer needs a welfare variable and a poverty line.");
    }
    if (layer === "diversification" && cropColumns.length === 0) {
      return setError("Diversification layer needs at least one crop/value column.");
    }
    setRunning(true);
    try {
      const id = await ensureSession();
      const res = await runExplorerSession(id);
      if (res.status === "failed") {
        setError(res.error_message || "Analysis failed.");
      } else {
        setResult(res);
        setNotice("Session saved & run. You can reload it any time from “Saved sessions”.");
      }
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Run failed. Check your inputs (boundaries, variables) and try again.");
    } finally {
      setRunning(false);
    }
  }

  async function handleSave() {
    setError(null);
    try {
      await ensureSession();
      setNotice("Session saved.");
    } catch {
      setError("Could not save session.");
    }
  }

  function loadSession(s: ExplorerSession) {
    setSessionId(s.id);
    setSessionName(s.name);
    setLayer(s.active_layer);
    setCountryIso3(s.country_iso3 || "");
    setAdminLevel(s.admin_level || "");
    const st = s.state || {};
    setGeoVariable(st.geo_variable || "");
    setWeightVariable(st.weight_variable || "");
    setWelfareVariable(st.welfare_variable || "");
    setPovertyLine(st.poverty_line || 0);
    setCropColumns(st.crop_columns || []);
    setFilters(st.filters || []);
    const ds = datasets.find((d) => d.id === s.dataset_id) || null;
    setDataset(ds);
    setResult(null);
    setNotice(`Loaded session “${s.name}”. Press Run to recompute.`);
  }

  const activeLayerMeta = LAYERS.find((l) => l.id === layer)!;
  const charts = (result?.charts || {}) as {
    rankings?: Record<string, unknown>[];
    morans_i?: { available?: boolean; moran_i?: number | null; p_value?: number | null; note?: string };
  };
  const rankings = charts.rankings || [];
  const morans = charts.morans_i || {};
  const geojson = result?.geojson as GeoJSON.FeatureCollection | undefined;

  return (
    <main className="max-w-6xl mx-auto px-4 py-12">
      <h1 className="text-4xl font-bold text-aic-dark mb-2">Interactive Spatial Explorer</h1>
      <p className="text-aic-muted mb-8 max-w-3xl">
        Load a dataset, choose an analytical layer, apply filters, and render an aggregated
        choropleth with Moran&apos;s I / LISA hotspot detection — recomputed live. Save a session
        to replay the exact exploration later. Only aggregated outputs are shown; raw microdata stays private.
      </p>

      {error && <div className="mb-6 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">{error}</div>}
      {notice && <div className="mb-6 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 text-sm">{notice}</div>}

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">Available datasets</h2>
        <DatasetGallery datasets={datasets} selectedId={dataset?.id} onSelect={setDataset} loading={datasetsLoading} />
      </section>

      <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
        {/* Controls */}
        <div className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Session name</label>
            <input value={sessionName} onChange={(e) => setSessionName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>

          <div>
            <span className="block text-xs font-semibold text-slate-500 mb-1">Analytical layer</span>
            <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
              {LAYERS.map((l) => (
                <button key={l.id} onClick={() => setLayer(l.id)}
                  className={"flex-1 rounded-md px-2 py-1.5 text-xs font-medium transition " +
                    (layer === l.id ? "bg-white text-aic-dark shadow" : "text-slate-500 hover:text-aic-dark")}>
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <Field label="Geography variable (admin unit column)">
            <VarSelect value={geoVariable} onChange={setGeoVariable} options={varNames} placeholder="Select column…" />
          </Field>

          <Field label="Weight variable (optional)">
            <VarSelect value={weightVariable} onChange={setWeightVariable} options={varNames} placeholder="None" allowEmpty />
          </Field>

          {layer === "poverty" && (
            <>
              <Field label="Welfare / consumption variable">
                <VarSelect value={welfareVariable} onChange={setWelfareVariable} options={varNames} placeholder="Select column…" />
              </Field>
              <Field label="Poverty line">
                <input type="number" value={povertyLine || ""} onChange={(e) => setPovertyLine(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="e.g. 700" />
              </Field>
            </>
          )}

          {layer === "agriculture" && (
            <p className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700">
              Agriculture uses this dataset&apos;s saved variable mapping (land_area, crop_output,
              crop_value, fertilizer, improved_seed…). Set it in the Variable Mapping panel first.
            </p>
          )}

          {layer === "diversification" && (
            <Field label="Crop / value columns (diversification is computed over their shares)">
              <MultiVarSelect values={cropColumns} onChange={setCropColumns} options={varNames} />
            </Field>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Field label="Boundary country ISO3">
              <input value={countryIso3} onChange={(e) => setCountryIso3(e.target.value.toUpperCase())}
                maxLength={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="e.g. RWA" />
            </Field>
            <Field label="Admin level">
              <select value={adminLevel} onChange={(e) => setAdminLevel(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                <option value="">None</option>
                {ADMIN_LEVELS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </Field>
          </div>

          {/* Filters */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-500">Filters</span>
              <button onClick={() => setFilters([...filters, { variable: varNames[0] || "", op: "eq", value: "" }])}
                className="text-xs font-medium text-aic-primary hover:underline">+ Add filter</button>
            </div>
            <div className="space-y-2">
              {filters.map((f, i) => (
                <div key={i} className="flex items-center gap-1">
                  <VarSelect value={f.variable} onChange={(v) => updateFilter(setFilters, filters, i, { variable: v })}
                    options={varNames} placeholder="col" small />
                  <select value={f.op} onChange={(e) => updateFilter(setFilters, filters, i, { op: e.target.value })}
                    className="rounded-md border border-slate-300 px-1 py-1.5 text-xs">
                    {FILTER_OPS.map((o) => <option key={o} value={o}>{o}</option>)}
                  </select>
                  <input value={String(f.value ?? "")} onChange={(e) => updateFilter(setFilters, filters, i, { value: e.target.value })}
                    className="w-20 rounded-md border border-slate-300 px-2 py-1.5 text-xs" placeholder="value" />
                  <button onClick={() => setFilters(filters.filter((_, j) => j !== i))}
                    className="text-slate-400 hover:text-red-500 text-sm px-1">×</button>
                </div>
              ))}
              {filters.length === 0 && <p className="text-xs text-slate-400">No filters — analysis runs on all rows.</p>}
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button onClick={handleRun} disabled={running}
              className="btn-primary flex-1 !py-2.5 text-sm disabled:opacity-60">
              {running ? "Running…" : "Run"}
            </button>
            <button onClick={handleSave} disabled={running}
              className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-aic-dark hover:bg-slate-50">
              Save
            </button>
          </div>

          {/* Saved sessions */}
          {sessions.length > 0 && (
            <div className="pt-2">
              <span className="text-xs font-semibold text-slate-500">Saved sessions</span>
              <ul className="mt-2 space-y-1">
                {sessions.map((s) => (
                  <li key={s.id}>
                    <button onClick={() => loadSession(s)}
                      className={"w-full truncate rounded-md px-2 py-1.5 text-left text-xs transition " +
                        (s.id === sessionId ? "bg-aic-primary/10 text-aic-dark" : "text-slate-600 hover:bg-slate-100")}>
                      {s.name} <span className="text-slate-400">· {s.active_layer}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Map + results */}
        <div className="space-y-6">
          {geojson && geojson.features?.length ? (
            <ChoroplethMap geojson={geojson} valueField={activeLayerMeta.valueField} label={activeLayerMeta.valueLabel}
              formatValue={layer === "poverty" ? (v) => (v * 100).toFixed(1) + "%" : (v) => v.toFixed(2)} />
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center h-80 text-aic-muted text-sm text-center px-8">
              {result
                ? "Analysis ran, but no boundary geometry was matched. Provide a boundary (country ISO3 + admin level, uploaded via Spatial Boundaries) whose admin names match your geography variable to render the choropleth. Rankings are shown below."
                : "Configure a layer on the left and press Run to render the interactive choropleth."}
            </div>
          )}

          {result && (
            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Admin units" value={String((result.summary_stats as Record<string, unknown>)?.n_units ?? rankings.length ?? "—")} />
              <Stat label="Moran's I" value={typeof morans.moran_i === "number" ? morans.moran_i.toFixed(3) : "n/a"} />
              <Stat label="Spatial p-value" value={typeof morans.p_value === "number" ? morans.p_value.toFixed(3) : "n/a"} />
            </div>
          )}

          {morans.note && <p className="text-xs text-slate-400">{morans.note}</p>}

          {rankings.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr><th className="px-4 py-2">Rank</th><th className="px-4 py-2">Admin unit</th><th className="px-4 py-2">{activeLayerMeta.valueLabel}</th></tr>
                </thead>
                <tbody>
                  {rankings.slice(0, 30).map((r, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-4 py-2 text-slate-400">{(r.rank as number) ?? i + 1}</td>
                      <td className="px-4 py-2 font-medium text-aic-dark">{String(r.admin_name ?? r.geo_value ?? "—")}</td>
                      <td className="px-4 py-2">{typeof r[activeLayerMeta.valueField] === "number"
                        ? (layer === "poverty" ? ((r[activeLayerMeta.valueField] as number) * 100).toFixed(1) + "%" : (r[activeLayerMeta.valueField] as number).toFixed(2))
                        : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result?.interpretation_text && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700 leading-relaxed">
              {result.interpretation_text}
            </div>
          )}

          {result?.job_id && (
            <AIPolicyBriefPanel jobId={result.job_id} defaultTitle={`Policy Brief — ${sessionName}`} />
          )}
        </div>
      </div>
    </main>
  );
}

function updateFilter(
  setFilters: (f: ExplorerFilter[]) => void,
  filters: ExplorerFilter[],
  i: number,
  patch: Partial<ExplorerFilter>,
) {
  setFilters(filters.map((f, j) => (j === i ? { ...f, ...patch } : f)));
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
      {children}
    </div>
  );
}

function VarSelect({ value, onChange, options, placeholder, allowEmpty, small }: {
  value: string; onChange: (v: string) => void; options: string[]; placeholder?: string; allowEmpty?: boolean; small?: boolean;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className={"rounded-lg border border-slate-300 text-sm " + (small ? "flex-1 px-1 py-1.5 text-xs" : "w-full px-3 py-2")}>
      <option value="">{placeholder || "Select…"}</option>
      {allowEmpty && value && <option value="">— clear —</option>}
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function MultiVarSelect({ values, onChange, options }: { values: string[]; onChange: (v: string[]) => void; options: string[] }) {
  function toggle(o: string) {
    onChange(values.includes(o) ? values.filter((v) => v !== o) : [...values, o]);
  }
  return (
    <div className="max-h-40 overflow-y-auto rounded-lg border border-slate-300 p-2 space-y-1">
      {options.length === 0 && <p className="text-xs text-slate-400">Select a dataset to list columns.</p>}
      {options.map((o) => (
        <label key={o} className="flex items-center gap-2 text-xs text-slate-700">
          <input type="checkbox" checked={values.includes(o)} onChange={() => toggle(o)} />
          {o}
        </label>
      ))}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-aic-dark">{value}</div>
    </div>
  );
}
