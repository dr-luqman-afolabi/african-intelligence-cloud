"use client";

import { useState } from "react";

interface SearchParams {
  q: string;
  source: string;
  year_from?: number;
  year_to?: number;
  max_results: number;
}

interface Props {
  onSearch: (params: SearchParams) => void;
  loading?: boolean;
  defaultQuery?: string;
}

const SOURCES = [
  { value: "openalex", label: "OpenAlex" },
  { value: "crossref", label: "Crossref" },
  { value: "semantic_scholar", label: "Semantic Scholar" },
];

export function SearchBar({ onSearch, loading, defaultQuery = "" }: Props) {
  const [q, setQ] = useState(defaultQuery);
  const [source, setSource] = useState("openalex");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    onSearch({
      q: q.trim(),
      source,
      year_from: yearFrom ? parseInt(yearFrom) : undefined,
      year_to: yearTo ? parseInt(yearTo) : undefined,
      max_results: 20,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search research papers, topics, authors..."
          className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-600"
        />
        <button
          type="submit"
          disabled={loading || !q.trim()}
          className="px-5 py-2.5 bg-slate-900 text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      <div className="flex flex-wrap gap-3 items-center text-sm">
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-green-600"
        >
          {SOURCES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="From year"
            value={yearFrom}
            onChange={(e) => setYearFrom(e.target.value)}
            min={1900}
            max={2100}
            className="w-28 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none"
          />
          <span className="text-slate-400">–</span>
          <input
            type="number"
            placeholder="To year"
            value={yearTo}
            onChange={(e) => setYearTo(e.target.value)}
            min={1900}
            max={2100}
            className="w-28 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none"
          />
        </div>
      </div>
    </form>
  );
}
