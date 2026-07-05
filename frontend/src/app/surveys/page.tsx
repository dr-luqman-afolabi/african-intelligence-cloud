"use client";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { fetchSurveys, SurveyEntry } from "@/lib/api";

function AccessBadge({ requiresApproval, redistributionAllowed }: { requiresApproval: boolean; redistributionAllowed: boolean }) {
  if (!requiresApproval && redistributionAllowed) {
    return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-green-100 text-green-800">Open</span>;
  }
  if (requiresApproval) {
    return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-yellow-100 text-yellow-800">Registration required</span>;
  }
  return <span className="px-1.5 py-0.5 rounded text-xs font-medium uppercase bg-blue-100 text-blue-800">Restricted</span>;
}

export default function SurveysPage() {
  const [surveys, setSurveys] = useState<SurveyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [topicFilter, setTopicFilter] = useState<string>("all");
  
  useEffect(() => {
    fetchSurveys()
      .then((data) => {
        setSurveys(data);
        setError(null);
      })
      .catch(() => setError("Failed to load survey catalog — is the backend running?"))
      .finally(() => setLoading(false));
  }, []);
  
  const topics = ["all", ...Array.from(new Set(surveys.map((s) => s.primary_topic)))];
  const filtered = topicFilter === "all" ? surveys : surveys.filter((s) => s.primary_topic === topicFilter);
  
  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
    <div>
    <h1 className="text-2xl font-bold text-slate-800">Microdata &amp; Survey Catalog</h1>
    <p className="text-sm text-slate-500 mt-0.5">
    Household, health, and census microdata series available for research (DHS, LSMS, IPUMS, MICS, and more).
    </p>
    </div>
    
      {error && (
      <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-red-700 text-sm">{error}</div>
    )}
    
    <div className="flex items-center gap-2 flex-wrap">
      {topics.map((t) => (
      <button
        key={t}
        onClick={() => setTopicFilter(t)}
        className={clsx(
          "px-4 py-1.5 rounded-full text-sm font-medium transition capitalize",
          topicFilter === t ? "bg-aic-dark text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          )}
        >
        {t}
      </button>
      ))}
    </div>
    
      {loading ? (
      <div className="text-center py-20 text-slate-400">Loading survey catalog…</div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.length === 0 && (
        <div className="text-center py-12 text-slate-400 col-span-2">No surveys match the current filter.</div>
      )}
        {filtered.map((s) => (
        <div key={s.survey_id} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
        <h2 className="font-semibold text-slate-800">{s.title}</h2>
        <AccessBadge requiresApproval={s.requires_approval} redistributionAllowed={s.redistribution_allowed} />
        </div>
        <div className="text-xs text-slate-400">
          {s.series} · {s.primary_topic}
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
        ))}
      </div>
    )}
    </div>
    );
}
