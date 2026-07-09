"use client";

import type { MicrodataDataset } from "@/lib/api";

const FILE_ICON: Record<string, string> = {
  csv: "📄",
  xlsx: "📊",
  dta: "📈",
  sav: "🧮",
};

function iconFor(ds: MicrodataDataset): string {
  return FILE_ICON[(ds.file_type || "").toLowerCase()] || "🗂️";
}

export interface DatasetGalleryProps {
  datasets: MicrodataDataset[];
  selectedId?: string | null;
  onSelect: (dataset: MicrodataDataset) => void;
  loading?: boolean;
}

/**
 * Shows the user's available microdata datasets as selectable icon cards.
 * Raw microdata is never rendered — only dataset-level metadata.
 */
export default function DatasetGallery({ datasets, selectedId, onSelect, loading }: DatasetGalleryProps) {
  if (loading) {
    return <div className="text-sm text-aic-muted py-6">Loading available datasets…</div>;
  }
  if (!datasets.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-aic-muted">
        No datasets available yet. Upload an LSMS/household survey file from the{" "}
        <a href="/datasets/upload" className="text-aic-primary underline">Datasets</a> page first.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {datasets.map((ds) => {
        const active = ds.id === selectedId;
        return (
          <button
            key={ds.id}
            onClick={() => onSelect(ds)}
            className={
              "flex flex-col items-start gap-2 rounded-xl border p-4 text-left transition " +
              (active
                ? "border-aic-primary bg-aic-primary/5 ring-2 ring-aic-primary/30"
                : "border-slate-200 bg-white hover:border-aic-primary/50 hover:bg-slate-50")
            }
          >
            <div className="flex w-full items-center justify-between">
              <span className="text-2xl" aria-hidden>{iconFor(ds)}</span>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                {ds.file_type}
              </span>
            </div>
            <div className="text-sm font-semibold text-aic-dark line-clamp-2">{ds.name}</div>
            <div className="text-xs text-aic-muted">
              {[ds.country_iso3, ds.survey_series, ds.year].filter(Boolean).join(" · ") || "—"}
            </div>
            <div className="text-[11px] text-slate-400">
              {(ds.row_count ?? "—")} rows · {(ds.column_count ?? "—")} cols
            </div>
          </button>
        );
      })}
    </div>
  );
}
