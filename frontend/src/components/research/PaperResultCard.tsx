"use client";

import Link from "next/link";
import { PaperResult } from "@/lib/api";

interface Props {
  paper: PaperResult;
}

export function PaperResultCard({ paper }: Props) {
  const authors =
    paper.authors.length > 3
      ? paper.authors.slice(0, 3).join(", ") + " et al."
      : paper.authors.join(", ");

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 hover:shadow-md transition space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {paper.doi ? (
            <Link
              href={`/research/papers/${encodeURIComponent(paper.doi)}`}
              className="text-base font-semibold text-slate-900 hover:text-green-700 leading-snug line-clamp-2"
            >
              {paper.title}
            </Link>
          ) : (
            <p className="text-base font-semibold text-slate-900 leading-snug line-clamp-2">
              {paper.title}
            </p>
          )}
        </div>
        {paper.is_open_access && (
          <span className="shrink-0 text-xs font-medium bg-green-50 text-green-700 border border-green-200 rounded-full px-2.5 py-0.5">
            Open Access
          </span>
        )}
      </div>

      {authors && (
        <p className="text-sm text-slate-500 truncate">{authors}</p>
      )}

      <div className="flex flex-wrap gap-3 text-xs text-slate-500">
        {paper.published_year && <span>{paper.published_year}</span>}
        {paper.journal && (
          <span className="italic truncate max-w-[200px]">{paper.journal}</span>
        )}
        {paper.citation_count > 0 && (
          <span>{paper.citation_count.toLocaleString()} citations</span>
        )}
      </div>

      {paper.abstract && (
        <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">
          {paper.abstract}
        </p>
      )}

      {paper.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {paper.topics.slice(0, 5).map((topic) => (
            <span
              key={topic}
              className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-0.5"
            >
              {topic}
            </span>
          ))}
        </div>
      )}

      {paper.open_access_url && (
        <div className="pt-1">
          <a
            href={paper.open_access_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-green-700 hover:underline"
          >
            View full text →
          </a>
        </div>
      )}
    </div>
  );
}
