"use client";

import { TheoryRecommendation } from "@/lib/api";

interface Props {
  theories: TheoryRecommendation[];
  title?: string;
}

export function TheoryPanel({ theories, title = "Recommended Theories" }: Props) {
  if (theories.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      <div className="space-y-3">
        {theories.map((t) => (
          <div
            key={t.name}
            className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1.5"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-900">{t.name}</span>
              <div className="flex gap-2 shrink-0">
                <span className="text-xs bg-blue-50 text-blue-700 rounded-full px-2 py-0.5">
                  Relevance: {Math.round(t.relevance_score * 100)}%
                </span>
                <span className="text-xs bg-green-50 text-green-700 rounded-full px-2 py-0.5">
                  Africa: {Math.round(t.african_relevance * 100)}%
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">{t.description}</p>
            <div className="w-full bg-slate-200 rounded-full h-1">
              <div
                className="bg-green-600 h-1 rounded-full"
                style={{ width: `${t.relevance_score * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
