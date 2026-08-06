"use client";

import { useState } from "react";
import clsx from "clsx";
import type { SurveyEntry } from "@/lib/api";

function AccessBadge({ requiresApproval, redistributionAllowed }: { requiresApproval: boolean; redistributionAllowed: boolean }) {
  if (!requiresApproval && redistributionAllowed) {
    return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-green-100 text-green-800">Open</span>;
  }
  if (requiresApproval) {
    return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-yellow-100 text-yellow-800">Registration required</span>;
  }
  return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-blue-100 text-blue-800">Restricted</span>;
}

export function formatTopic(topic: string) {
  return topic
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function SurveyCard({ s }: { s: SurveyEntry }) {
  return (
    <div className="card card-hover p-5 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-semibold text-slate-800">{s.title}</h2>
        <AccessBadge requiresApproval={s.requires_approval} redistributionAllowed={s.redistribution_allowed} />
      </div>
      <div className="text-xs text-slate-400">
        {s.series} · {formatTopic(s.primary_topic)}
        {s.country_iso3 ? ` · ${s.country_iso3}` : ""}
      </div>
      {s.microdata_available && (
        <div className="text-xs text-green-700 font-medium">Microdata available</div>
      )}
      <div className="flex flex-wrap gap-1.5">
        {(s.tags || []).map((tag) => (
          <span key={tag} className="px-1.5 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
            {tag}
          </span>
        ))}
      </div>
      <div className="flex gap-4 mt-2 text-sm">
        {s.access_url && (
          <a href={s.access_url} target="_blank" rel="noreferrer" className="text-aic-green hover:underline">
            Access data ↗
          </a>
        )}
        {s.documentation_url && (
          <a href={s.documentation_url} target="_blank" rel="noreferrer" className="text-slate-500 hover:underline">
            Documentation ↗
          </a>
        )}
      </div>
    </div>
  );
}

/**
 * Filtering only. The full catalogue is rendered server-side by the parent and
 * passed in, so crawlers get every survey in the initial HTML; this just hides
 * rows on click.
 */
export default function SurveyCatalog({ surveys }: { surveys: SurveyEntry[] }) {
  const [topicFilter, setTopicFilter] = useState<string>("all");
  const topics = ["all", ...Array.from(new Set(surveys.map((s) => s.primary_topic)))];
  const filtered = topicFilter === "all" ? surveys : surveys.filter((s) => s.primary_topic === topicFilter);

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap">
        {topics.map((t) => (
          <button
            key={t}
            onClick={() => setTopicFilter(t)}
            className={clsx(
              "px-4 py-1.5 rounded-full text-sm font-medium transition capitalize",
              topicFilter === t ? "bg-aic-dark text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200",
            )}
          >
            {formatTopic(t)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400 col-span-2">No surveys match the current filter.</div>
        )}
        {filtered.map((s) => (
          <SurveyCard key={s.survey_id} s={s} />
        ))}
      </div>
    </>
  );
}
