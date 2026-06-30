"use client";

import { AfricanDataset } from "@/lib/api";

interface Props {
  datasets: AfricanDataset[];
  title?: string;
}

export function DatasetPanel({ datasets, title = "Recommended African Datasets" }: Props) {
  if (datasets.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      <div className="space-y-3">
        {datasets.map((d) => (
          <div
            key={d.name}
            className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1.5"
          >
            <div className="flex items-start justify-between gap-2">
              <a
                href={d.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-semibold text-green-700 hover:underline leading-snug"
              >
                {d.name}
              </a>
              <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 rounded-full px-2 py-0.5 shrink-0 whitespace-nowrap">
                {d.license}
              </span>
            </div>
            <p className="text-xs text-slate-500">{d.coverage}</p>
            <p className="text-xs text-slate-600 italic">{d.variables}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
