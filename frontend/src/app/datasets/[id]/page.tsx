"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchDataset, triggerProfiling, deleteDataset, DatasetDetail, DatasetStatus } from "@/lib/api";

const STATUS_STYLES: Record<DatasetStatus, string> = {
  uploaded: "bg-blue-100 text-blue-800",
  profiling: "bg-yellow-100 text-yellow-800",
  profiled: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 rounded-lg p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-1">{label}</div>
      <div className="text-xl font-bold text-slate-800">{value}</div>
    </div>
  );
}

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [profilingMsg, setProfilingMsg] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchDataset(id)
      .then(setDataset)
      .catch(() => setError("Dataset not found or access denied."))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleProfile() {
    if (!dataset) return;
    setProfilingMsg("");
    try {
      await triggerProfiling(dataset.id);
      setProfilingMsg("Profiling started. Refresh in a moment to see results.");
      setDataset((d) => d ? { ...d, status: "profiling" } : d);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setProfilingMsg(detail ?? "Failed to start profiling.");
    }
  }

  async function handleDelete() {
    if (!dataset || deleting) return;
    setDeleting(true);
    try {
      await deleteDataset(dataset.id);
      router.push("/datasets");
    } catch {
      setDeleting(false);
      setConfirmDelete(false);
      setError("Failed to delete dataset.");
    }
  }

  if (loading) return <div className="text-center py-20 text-slate-400">Loading…</div>;
  if (error || !dataset)
    return (
      <div className="max-w-3xl mx-auto px-4 py-10 text-center">
        <p className="text-red-600">{error || "Dataset not found."}</p>
        <Link href="/datasets" className="mt-4 inline-block text-green-700 hover:underline">
          Back to Datasets
        </Link>
      </div>
    );

  const { profile, columns } = dataset;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
            <Link href="/datasets" className="hover:text-green-700">Datasets</Link>
            <span>/</span>
            <span className="text-slate-700">{dataset.name}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">{dataset.name}</h1>
          {dataset.description && (
            <p className="text-slate-500 text-sm mt-1">{dataset.description}</p>
          )}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[dataset.status]}`}>
              {dataset.status}
            </span>
            <span className="text-xs text-slate-500 capitalize">{dataset.privacy}</span>
            <span className="text-xs text-slate-400">{dataset.file_extension.toUpperCase()}</span>
            <span className="text-xs text-slate-400">{formatBytes(dataset.file_size_bytes)}</span>
            {dataset.tags.map((t) => (
              <span key={t} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
                {t}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {dataset.status !== "profiling" && (
            <button
              onClick={handleProfile}
              className="px-3 py-1.5 text-sm bg-blue-700 text-white rounded-lg hover:bg-blue-800 transition"
            >
              {dataset.status === "profiled" ? "Re-profile" : "Run Profile"}
            </button>
          )}
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition"
            >
              Delete
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-600">Confirm?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-60"
              >
                {deleting ? "Deleting…" : "Yes, delete"}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {profilingMsg && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 rounded-lg text-sm">
          {profilingMsg}
        </div>
      )}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {/* Profile summary */}
      {profile && (
        <div>
          <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
            Profile Summary
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat label="Rows" value={profile.row_count.toLocaleString()} />
            <Stat label="Columns" value={profile.column_count} />
            <Stat label="Missing cells" value={`${profile.missing_cells_pct.toFixed(1)}%`} />
            <Stat label="Duplicate rows" value={profile.duplicate_rows.toLocaleString()} />
            <Stat label="Numeric cols" value={profile.numeric_columns} />
            <Stat label="Categorical cols" value={profile.categorical_columns} />
            <Stat label="Datetime cols" value={profile.datetime_columns} />
            <Stat label="Profiling time" value={`${profile.profiling_duration_ms} ms`} />
          </div>
        </div>
      )}

      {/* Columns table */}
      {columns.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
            Columns ({columns.length})
          </h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Column</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Type</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Nulls</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Null %</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Unique</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Mean</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Sample values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {columns.map((col) => (
                  <tr key={col.column_name} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-mono text-slate-800 text-xs">{col.column_name}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs capitalize">{col.data_type}</td>
                    <td className="px-4 py-3 text-slate-500 text-right">{col.null_count}</td>
                    <td className="px-4 py-3 text-slate-500 text-right">{col.null_pct.toFixed(1)}%</td>
                    <td className="px-4 py-3 text-slate-500 text-right">
                      {col.unique_count ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-right">
                      {col.mean_value != null ? col.mean_value.toFixed(2) : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs font-mono max-w-xs truncate">
                      {col.sample_values.slice(0, 3).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!profile && dataset.status === "uploaded" && (
        <div className="text-center py-10 text-slate-400 text-sm border border-dashed border-slate-200 rounded-xl">
          No profile yet. Click <strong>Run Profile</strong> to analyse this dataset.
        </div>
      )}

      <div className="text-xs text-slate-400 pt-2">
        Uploaded {new Date(dataset.created_at).toLocaleString()} · Original file:{" "}
        {dataset.original_filename}
      </div>
    </div>
  );
}
