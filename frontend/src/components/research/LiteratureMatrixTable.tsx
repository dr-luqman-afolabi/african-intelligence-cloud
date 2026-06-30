"use client";

import { useState } from "react";
import { LiteratureMatrixRow } from "@/lib/api";

interface Props {
  rows: LiteratureMatrixRow[];
}

type SortKey = "year" | "citation_count" | "title";

export function LiteratureMatrixTable({ rows }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("citation_count");
  const [asc, setAsc] = useState(false);

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    if (typeof av === "string" && typeof bv === "string") {
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return asc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function toggle(key: SortKey) {
    if (sortKey === key) {
      setAsc(!asc);
    } else {
      setSortKey(key);
      setAsc(false);
    }
  }

  const SortBtn = ({ k, label }: { k: SortKey; label: string }) => (
    <button
      onClick={() => toggle(k)}
      className="flex items-center gap-1 hover:text-green-700 transition"
    >
      {label}
      <span className="text-slate-400">
        {sortKey === k ? (asc ? "↑" : "↓") : "↕"}
      </span>
    </button>
  );

  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
        No papers to display.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 min-w-[260px]">
                <SortBtn k="title" label="Title" />
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 whitespace-nowrap">
                Authors
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 whitespace-nowrap">
                <SortBtn k="year" label="Year" />
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 whitespace-nowrap">
                Journal
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 whitespace-nowrap">
                <SortBtn k="citation_count" label="Citations" />
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700 whitespace-nowrap">
                OA
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700">
                Topics
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sorted.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50 transition">
                <td className="px-4 py-3">
                  {row.doi ? (
                    <a
                      href={`https://doi.org/${row.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-slate-900 hover:text-green-700 line-clamp-2"
                    >
                      {row.title}
                    </a>
                  ) : (
                    <span className="font-medium text-slate-900 line-clamp-2">
                      {row.title}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500 max-w-[150px]">
                  <span className="truncate block">
                    {row.authors.slice(0, 2).join(", ")}
                    {row.authors.length > 2 && " et al."}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                  {row.year ?? "—"}
                </td>
                <td className="px-4 py-3 text-slate-500 max-w-[160px]">
                  <span className="truncate block italic">{row.journal ?? "—"}</span>
                </td>
                <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                  {row.citation_count.toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  {row.is_open_access ? (
                    <span className="text-xs bg-green-50 text-green-700 rounded-full px-2 py-0.5">
                      Yes
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">No</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {row.topics.slice(0, 3).map((t) => (
                      <span
                        key={t}
                        className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
