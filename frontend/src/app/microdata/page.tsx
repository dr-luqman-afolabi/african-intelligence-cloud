"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  uploadMicrodata,
  fetchMicrodataDatasets,
  fetchMicrodataVariables,
  type MicrodataDataset,
  type MicrodataVariable,
} from "@/lib/api";
import VariableMappingPanel from "@/components/microdata/VariableMappingPanel";
import MicrodataDashboardPanel from "@/components/microdata/MicrodataDashboardPanel";

const ACCEPTED_EXTENSIONS = ".csv,.xlsx,.dta,.sav,.zip";

export default function MicrodataPage() {
  const router = useRouter();

  const [datasets, setDatasets] = useState<MicrodataDataset[]>([]);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [countryIso3, setCountryIso3] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const [selectedDataset, setSelectedDataset] = useState<MicrodataDataset | null>(null);
  const [variables, setVariables] = useState<MicrodataVariable[]>([]);
  const [loadingVariables, setLoadingVariables] = useState(false);

  const [welfareVariable, setWelfareVariable] = useState("");
  const [weightVariable, setWeightVariable] = useState("");
  const [geographyVariable, setGeographyVariable] = useState("");
  const [povertyLine, setPovertyLine] = useState("");
  const [groupByVars, setGroupByVars] = useState<string[]>([]);
  const [cropColumns, setCropColumns] = useState<string[]>([]);
  const [hasSavedMapping, setHasSavedMapping] = useState(false);

  async function loadDatasets() {
    setLoadingDatasets(true);
    setDatasetsError(null);
    try {
      const res = await fetchMicrodataDatasets();
      setDatasets(res.items);
    } catch {
      setDatasetsError("Could not load datasets. Please try again.");
    } finally {
      setLoadingDatasets(false);
    }
  }

  useEffect(() => {
    loadDatasets();
  }, []);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !name) {
      setUploadError("Please provide a dataset name and choose a file.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);
      if (countryIso3) formData.append("country_iso3", countryIso3);

      const dataset = await uploadMicrodata(formData);
      setUploadSuccess('Uploaded "' + dataset.name + '" successfully.');
      setName("");
      setCountryIso3("");
      setFile(null);
      await loadDatasets();
    } catch {
      setUploadError("Upload failed. Please check the file format and try again.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSelectDataset(dataset: MicrodataDataset) {
    setSelectedDataset(dataset);
    setVariables([]);
    setWelfareVariable("");
    setWeightVariable("");
    setGeographyVariable("");
    setGroupByVars([]);
    setCropColumns([]);
    setHasSavedMapping(false);
    setLoadingVariables(true);
    try {
      const vars = await fetchMicrodataVariables(dataset.id);
      setVariables(vars);
    } catch {
      setVariables([]);
    } finally {
      setLoadingVariables(false);
    }
  }

  function toggleGroupBy(variableName: string) {
    setGroupByVars((prev) =>
      prev.includes(variableName)
        ? prev.filter((v) => v !== variableName)
        : [...prev, variableName]
    );
  }

  function buildParams() {
    const params = new URLSearchParams();
    if (!selectedDataset) return params;
    params.set("dataset_id", selectedDataset.id);
    params.set("welfare_variable", welfareVariable);
    params.set("poverty_line", povertyLine);
    if (weightVariable) params.set("weight_variable", weightVariable);
    if (groupByVars.length > 0) params.set("group_by", groupByVars.join(","));
    return params;
  }

  function handleRunPoverty() {
    if (!selectedDataset || !welfareVariable || !povertyLine) return;
    const params = buildParams();
    router.push("/microdata/poverty?" + params.toString());
  }

  function handleRunSpatial() {
    if (!selectedDataset || !welfareVariable || !povertyLine || !geographyVariable) return;
    const params = buildParams();
    params.set("geo_variable", geographyVariable);
    router.push("/microdata/spatial?" + params.toString());
  }

  function handleRunAgriculture() {
    if (!selectedDataset) return;
    const params = new URLSearchParams();
    params.set("dataset_id", selectedDataset.id);
    if (weightVariable) params.set("weight_variable", weightVariable);
    if (groupByVars.length > 0) params.set("group_by", groupByVars.join(","));
    router.push("/microdata/agriculture?" + params.toString());
  }

  function handleRunDiversification() {
    if (!selectedDataset || cropColumns.length < 2) return;
    const params = new URLSearchParams();
    params.set("dataset_id", selectedDataset.id);
    params.set("crop_columns", cropColumns.join(","));
    if (weightVariable) params.set("weight_variable", weightVariable);
    if (groupByVars.length > 0) params.set("group_by", groupByVars.join(","));
    router.push("/microdata/diversification?" + params.toString());
  }

  function toggleCropColumn(variableName: string) {
    setCropColumns((prev) =>
      prev.includes(variableName) ? prev.filter((v) => v !== variableName) : [...prev, variableName]
    );
  }

  const canRunPoverty = Boolean(selectedDataset && welfareVariable && povertyLine);
  const canRunSpatial = Boolean(
    selectedDataset && welfareVariable && povertyLine && geographyVariable
  );
  const canRunAgriculture = Boolean(selectedDataset && hasSavedMapping);
  const canRunDiversification = Boolean(selectedDataset && cropColumns.length >= 2);

  return (
    <main className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-aic-dark mb-4">Microdata Studio</h1>
      <p className="text-aic-muted mb-10">
        Upload household survey microdata (EICV, UNPS, DHS, LSMS, MICS, Afrobarometer, and more)
        and run poverty, inequality, and spatial analysis directly from your dashboard.
      </p>

      <section className="mb-10">
        <h2 className="text-xl font-semibold text-aic-dark mb-1">Interactive dashboard</h2>
        <p className="text-sm text-aic-muted mb-4">
          Pick a dataset and variables, then run an instant poverty analysis with bar, line, pie,
          or map output — no page reload needed.
        </p>
        <MicrodataDashboardPanel />
      </section>

      <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
        <h2 className="text-xl font-semibold text-aic-dark mb-4">Upload a dataset</h2>
        <form onSubmit={handleUpload} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-1">
            <label className="block text-sm font-medium text-aic-dark mb-1">Dataset name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border border-slate-300 rounded-lg px-3 py-2 w-full"
              placeholder="e.g. EICV5 Household"
            />
          </div>
          <div className="sm:col-span-1">
            <label className="block text-sm font-medium text-aic-dark mb-1">Country (ISO3)</label>
            <input
              type="text"
              value={countryIso3}
              onChange={(e) => setCountryIso3(e.target.value.toUpperCase())}
              maxLength={3}
              className="border border-slate-300 rounded-lg px-3 py-2 w-full"
              placeholder="e.g. RWA"
            />
          </div>
          <div className="sm:col-span-1">
            <label className="block text-sm font-medium text-aic-dark mb-1">
              File (.csv, .xlsx, .dta, .sav, or .zip)
            </label>
            <input
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="border border-slate-300 rounded-lg px-3 py-2 w-full bg-white"
            />
          </div>
          <div className="sm:col-span-3 flex items-center gap-4">
            <button
              type="submit"
              disabled={uploading}
              className="bg-aic-green text-white px-5 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              {uploading ? "Uploading..." : "Upload dataset"}
            </button>
            {uploadError && <p className="text-aic-red text-sm">{uploadError}</p>}
            {uploadSuccess && <p className="text-aic-green text-sm">{uploadSuccess}</p>}
          </div>
        </form>
      </section>

      <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-10">
        <h2 className="text-xl font-semibold text-aic-dark mb-4">Your datasets</h2>
        {loadingDatasets ? (
          <p className="text-aic-muted">Loading datasets...</p>
        ) : datasetsError ? (
          <p className="text-aic-red">{datasetsError}</p>
        ) : datasets.length === 0 ? (
          <p className="text-aic-muted">No datasets uploaded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="text-aic-muted border-b border-slate-200">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Country</th>
                  <th className="py-2 pr-4">Rows</th>
                  <th className="py-2 pr-4">Columns</th>
                  <th className="py-2 pr-4">Access</th>
                  <th className="py-2 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4">{d.name}</td>
                    <td className="py-2 pr-4">{d.country_iso3 ?? "—"}</td>
                    <td className="py-2 pr-4">{d.row_count ?? "—"}</td>
                    <td className="py-2 pr-4">{d.column_count ?? "—"}</td>
                    <td className="py-2 pr-4">{d.access_status}</td>
                    <td className="py-2 pr-4">
                      <button
                        onClick={() => handleSelectDataset(d)}
                        className={
                          "px-3 py-1 rounded-lg text-sm font-medium border " +
                          (selectedDataset?.id === d.id
                            ? "bg-aic-green text-white border-aic-green"
                            : "border-slate-300 text-aic-dark")
                        }
                      >
                        {selectedDataset?.id === d.id ? "Selected" : "Select"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedDataset && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <h2 className="text-xl font-semibold text-aic-dark mb-4">
            Configure analysis for &quot;{selectedDataset.name}&quot;
          </h2>
          {loadingVariables ? (
            <p className="text-aic-muted">Loading variables...</p>
          ) : variables.length === 0 ? (
            <p className="text-aic-muted">No variables found for this dataset.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-aic-dark mb-1">
                  Welfare variable
                </label>
                <select
                  value={welfareVariable}
                  onChange={(e) => setWelfareVariable(e.target.value)}
                  className="border border-slate-300 rounded-lg px-3 py-2 w-full"
                >
                  <option value="">Select variable</option>
                  {variables.map((v) => (
                    <option key={v.id} value={v.variable_name}>
                      {v.variable_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-aic-dark mb-1">
                  Weight variable (optional)
                </label>
                <select
                  value={weightVariable}
                  onChange={(e) => setWeightVariable(e.target.value)}
                  className="border border-slate-300 rounded-lg px-3 py-2 w-full"
                >
                  <option value="">None</option>
                  {variables.map((v) => (
                    <option key={v.id} value={v.variable_name}>
                      {v.variable_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-aic-dark mb-1">
                  Geography variable
                </label>
                <select
                  value={geographyVariable}
                  onChange={(e) => setGeographyVariable(e.target.value)}
                  className="border border-slate-300 rounded-lg px-3 py-2 w-full"
                >
                  <option value="">Select variable</option>
                  {variables.map((v) => (
                    <option key={v.id} value={v.variable_name}>
                      {v.variable_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-aic-dark mb-1">
                  Poverty line
                </label>
                <input
                  type="number"
                  value={povertyLine}
                  onChange={(e) => setPovertyLine(e.target.value)}
                  className="border border-slate-300 rounded-lg px-3 py-2 w-full"
                  placeholder="e.g. 159375"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-aic-dark mb-2">
                  Group by (optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {variables.map((v) => (
                    <button
                      type="button"
                      key={v.id}
                      onClick={() => toggleGroupBy(v.variable_name)}
                      className={
                        "px-3 py-1 rounded-full text-sm border " +
                        (groupByVars.includes(v.variable_name)
                          ? "bg-aic-green text-white border-aic-green"
                          : "border-slate-300 text-aic-dark")
                      }
                    >
                      {v.variable_name}
                    </button>
                  ))}
                </div>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-aic-dark mb-2">
                  Crop / income source columns (for diversification — select 2+)
                </label>
                <div className="flex flex-wrap gap-2">
                  {variables.map((v) => (
                    <button
                      type="button"
                      key={v.id}
                      onClick={() => toggleCropColumn(v.variable_name)}
                      className={
                        "px-3 py-1 rounded-full text-sm border " +
                        (cropColumns.includes(v.variable_name)
                          ? "bg-aic-dark text-white border-aic-dark"
                          : "border-slate-300 text-aic-dark")
                      }
                    >
                      {v.variable_name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleRunPoverty}
              disabled={!canRunPoverty}
              className="bg-aic-green text-white px-5 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              Run poverty analysis
            </button>
            <button
              onClick={handleRunSpatial}
              disabled={!canRunSpatial}
              className="bg-aic-dark text-white px-5 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              Run spatial analysis
            </button>
            <button
              onClick={handleRunAgriculture}
              disabled={!canRunAgriculture}
              title={canRunAgriculture ? "" : "Save a variable mapping below first (needs land_area / crop_output / crop_value etc.)"}
              className="bg-aic-green text-white px-5 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              Run agriculture analysis
            </button>
            <button
              onClick={handleRunDiversification}
              disabled={!canRunDiversification}
              title={canRunDiversification ? "" : "Select at least two crop/income source columns above"}
              className="bg-aic-dark text-white px-5 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              Run diversification analysis
            </button>
          </div>
        </section>
      )}

      {selectedDataset && variables.length > 0 && (
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mt-10">
          <h2 className="text-xl font-semibold text-aic-dark mb-1">Variable mapping</h2>
          <p className="text-sm text-aic-muted mb-4">
            Map this survey&apos;s raw columns to standard concepts (household ID, welfare, gender,
            district, land area, ...) so agriculture and cross-survey analyses can run without
            knowing each survey&apos;s own naming conventions.
          </p>
          <VariableMappingPanel
            datasetId={selectedDataset.id}
            variables={variables}
            onSaved={() => setHasSavedMapping(true)}
            onLoadedExisting={() => setHasSavedMapping(true)}
          />
        </section>
      )}
    </main>
  );
}
