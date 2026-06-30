"use client";

import { useState } from "react";
import { exportResearchPapers, LiteratureMatrixRow } from "@/lib/api";

interface Props {
  papers: LiteratureMatrixRow[];
  disabled?: boolean;
}

type Format = "bibtex" | "ris" | "excel" | "csv";

const FORMAT_OPTIONS: { value: Format; label: string; ext: string; mime: string }[] = [
  { value: "bibtex", label: "BibTeX (.bib)", ext: "references.bib", mime: "text/plain" },
  { value: "ris", label: "RIS (.ris)", ext: "references.ris", mime: "text/plain" },
  { value: "excel", label: "Excel (.xlsx)", ext: "literature_matrix.xlsx", mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  { value: "csv", label: "CSV (.csv)", ext: "literature_matrix.csv", mime: "text/csv" },
];

export function ExportButton({ papers, disabled }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<Format | null>(null);

  async function handleExport(format: Format, ext: string) {
    if (papers.length === 0) return;
    setLoading(format);
    setOpen(false);
    try {
      const blob = await exportResearchPapers({ papers, format });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = ext;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
      alert("Export failed. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        disabled={disabled || papers.length === 0 || loading !== null}
        className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
      >
        {loading ? "Exporting…" : "Export"}
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 mt-1 w-44 z-20 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
            {FORMAT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleExport(opt.value, opt.ext)}
                className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
