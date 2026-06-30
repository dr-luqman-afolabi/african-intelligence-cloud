"use client";

import { MethodRecommendation } from "@/lib/api";

interface Props {
  methods: MethodRecommendation[];
  title?: string;
}

export function MethodPanel({ methods, title = "Recommended Methods" }: Props) {
  if (methods.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      <div className="space-y-3">
        {methods.map((m) => (
          <div
            key={m.method}
            className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-900">{m.method}</span>
              <span className="text-xs bg-purple-50 text-purple-700 rounded-full px-2 py-0.5 shrink-0">
                {Math.round(m.relevance_score * 100)}% match
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">{m.description}</p>
            <div className="flex flex-wrap gap-1.5">
              {m.software.map((sw) => (
                <span
                  key={sw}
                  className="text-xs font-mono bg-white border border-slate-200 text-slate-600 rounded px-1.5 py-0.5"
                >
                  {sw}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
