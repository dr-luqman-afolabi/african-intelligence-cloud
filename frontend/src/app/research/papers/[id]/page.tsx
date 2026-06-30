"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchResearchPaper, StoredPaper } from "@/lib/api";
import { CitationPanel } from "@/components/research/CitationPanel";

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<StoredPaper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchResearchPaper(decodeURIComponent(id))
      .then(setPaper)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load paper"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-sm text-slate-400">Loading paper…</p>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-sm text-red-600">{error ?? "Paper not found."}</p>
          <Link href="/research/search" className="text-sm text-green-700 hover:underline">
            Back to search
          </Link>
        </div>
      </div>
    );
  }

  const authors =
    paper.authors.length > 0
      ? paper.authors.map((a) => a.full_name).join(", ")
      : "Unknown authors";

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-6 py-4 flex items-center gap-3">
        <Link href="/research/search" className="text-slate-400 hover:text-slate-600 transition text-sm">
          ← Search
        </Link>
        <span className="text-slate-300">/</span>
        <span className="text-base font-semibold text-slate-800 truncate">Paper Detail</span>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-1 space-y-2">
              <h1 className="text-xl font-bold text-slate-900 leading-snug">{paper.title}</h1>
              <p className="text-sm text-slate-500">{authors}</p>
            </div>
            {paper.is_open_access && (
              <span className="shrink-0 text-xs font-medium bg-green-50 text-green-700 border border-green-200 rounded-full px-3 py-1">
                Open Access
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-slate-500 border-t border-slate-100 pt-4">
            {paper.published_year && (
              <span><span className="font-medium text-slate-700">Year:</span> {paper.published_year}</span>
            )}
            {paper.journal && (
              <span><span className="font-medium text-slate-700">Journal:</span> <em>{paper.journal}</em></span>
            )}
            {paper.citation_count > 0 && (
              <span><span className="font-medium text-slate-700">Citations:</span> {paper.citation_count.toLocaleString()}</span>
            )}
            {paper.doi && (
              <span>
                <span className="font-medium text-slate-700">DOI:</span>{" "}
                <a
                  href={`https://doi.org/${paper.doi}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-green-700 hover:underline"
                >
                  {paper.doi}
                </a>
              </span>
            )}
          </div>

          {paper.open_access_url && (
            <a
              href={paper.open_access_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-sm text-white bg-green-700 hover:bg-green-800 rounded-xl px-4 py-2 transition"
            >
              Read full text →
            </a>
          )}
        </div>

        {/* Abstract */}
        {paper.abstract && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-2">
            <h2 className="text-sm font-semibold text-slate-700">Abstract</h2>
            <p className="text-sm text-slate-600 leading-relaxed">{paper.abstract}</p>
          </div>
        )}

        {/* Tags row */}
        {(paper.topics.length > 0 || paper.methods.length > 0 || paper.theories.length > 0 || paper.policy_areas.length > 0) && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
            {paper.topics.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Topics</p>
                <div className="flex flex-wrap gap-1.5">
                  {paper.topics.map((t) => (
                    <span key={t} className="text-xs bg-slate-100 text-slate-600 rounded-full px-2.5 py-0.5">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {paper.methods.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Methods</p>
                <div className="flex flex-wrap gap-1.5">
                  {paper.methods.map((m) => (
                    <span key={m} className="text-xs bg-purple-50 text-purple-700 rounded-full px-2.5 py-0.5">{m}</span>
                  ))}
                </div>
              </div>
            )}
            {paper.theories.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Theories</p>
                <div className="flex flex-wrap gap-1.5">
                  {paper.theories.map((th) => (
                    <span key={th} className="text-xs bg-blue-50 text-blue-700 rounded-full px-2.5 py-0.5">{th}</span>
                  ))}
                </div>
              </div>
            )}
            {paper.policy_areas.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Policy Areas</p>
                <div className="flex flex-wrap gap-1.5">
                  {paper.policy_areas.map((p) => (
                    <span key={p} className="text-xs bg-amber-50 text-amber-700 rounded-full px-2.5 py-0.5">{p}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Authors */}
        {paper.authors.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
            <h2 className="text-sm font-semibold text-slate-700">Authors</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {paper.authors.map((a, i) => (
                <div key={i} className="rounded-xl bg-slate-50 px-4 py-3">
                  <p className="text-sm font-medium text-slate-900">{a.full_name}</p>
                  {a.affiliation && (
                    <p className="text-xs text-slate-500 mt-0.5">{a.affiliation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Citations */}
        <CitationPanel citations={paper.citations} />
      </div>
    </div>
  );
}
