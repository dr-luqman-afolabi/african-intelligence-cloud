"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchDatasets, DatasetListItem, DatasetStatus } from "@/lib/api";

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

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    fetchDatasets(page, PAGE_SIZE)
      .then((resp) => {
        setDatasets(resp.items);
        setTotal(resp.total);
      })
      .catch(() => setError("Failed to load datasets."))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Datasets</h1>
          <p className="text-sm text-slate-500 mt-1">{total} dataset{total !== 1 ? "s" : ""} available</p>
        </div>
        <Link
          href="/datasets/upload"
          className="px-4 py-2 bg-green-700 text-white text-sm rounded-lg hover:bg-green-800 transition font-medium"
        >
          + Upload Dataset
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">Loading…</div>
      ) : datasets.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          No datasets yet.{" "}
          <Link href="/datasets/upload" className="text-green-700 hover:underline">
            Upload your first dataset.
          </Link>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Name</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Extension</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Size</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Rows</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Privacy</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Uploaded</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasets.map((ds) => (
                  <tr key={ds.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3">
                      <Link
                        href={`/datasets/${ds.id}`}
                        className="font-medium text-slate-900 hover:text-green-700 transition"
                      >
                        {ds.name}
                      </Link>
                      {ds.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {ds.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500 uppercase font-mono text-xs">
                      {ds.file_extension}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{formatBytes(ds.file_size_bytes)}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {ds.row_count != null ? ds.row_count.toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500 capitalize">{ds.privacy}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[ds.status]}`}
                      >
                        {ds.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {new Date(ds.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-slate-500">
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
