"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { fetchConsumptionCatalog, type ConsumptionCatalog } from "@/lib/api";

function formatSize(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function HouseholdConsumptionPage() {
  const [catalog, setCatalog] = useState<ConsumptionCatalog | null>(null);
  const [country, setCountry] = useState("all");
  const [survey, setSurvey] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchConsumptionCatalog()
      .then(setCatalog)
      .catch(() => setError("The household consumption catalog could not be loaded."))
      .finally(() => setLoading(false));
  }, []);

  const datasets = useMemo(() => {
    if (!catalog) return [];
    const needle = query.trim().toLowerCase();
    return catalog.datasets.filter((item) =>
      (country === "all" || item.country_iso3 === country) &&
      (survey === "all" || item.survey === survey) &&
      (!needle || [item.country, item.country_iso3, item.survey, item.wave, item.years]
        .some((value) => value.toLowerCase().includes(needle)))
    );
  }, [catalog, country, survey, query]);

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="border-b border-slate-200 bg-aic-dark text-white">
        <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">Food security · welfare · poverty</p>
          <h1 className="mt-3 max-w-4xl text-3xl font-bold tracking-tight sm:text-5xl">Household Consumption Observatory</h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300">Harmonized food-consumption values by purchases, own production, and gifts across African household surveys—with transparent construction decisions and source-level provenance.</p>
          {catalog && <div className="mt-8 flex flex-wrap gap-3"><span className="rounded-full bg-white/10 px-4 py-2 text-sm"><strong>{catalog.total_dataset_count}</strong> datasets</span><span className="rounded-full bg-white/10 px-4 py-2 text-sm"><strong>{catalog.country_count}</strong> countries</span><span className="rounded-full bg-white/10 px-4 py-2 text-sm"><strong>{catalog.surveys.length}</strong> survey programmes</span><span className="rounded-full bg-white/10 px-4 py-2 text-sm">2017 PPP comparable values</span></div>}
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6">
        {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
        {loading && <div className="card p-10 text-center text-aic-muted">Loading consumption catalog…</div>}

        {catalog && <>
          <section className="grid gap-5 lg:grid-cols-3">
            <article className="card p-6"><span className="grid h-9 w-9 place-items-center rounded-lg bg-emerald-100 font-bold text-emerald-700">01</span><h2 className="mt-4 font-bold text-aic-dark">Comparable valuation</h2><p className="mt-2 text-sm leading-6 text-aic-muted">Purchases use reported prices; production and gifts use local median purchase prices where observations are sufficient.</p></article>
            <article className="card p-6"><span className="grid h-9 w-9 place-items-center rounded-lg bg-blue-100 font-bold text-blue-700">02</span><h2 className="mt-4 font-bold text-aic-dark">Consistent time basis</h2><p className="mt-2 text-sm leading-6 text-aic-muted">Recall periods are annualized, multi-visit surveys are averaged, and local values are converted to 2017 PPP.</p></article>
            <article className="card p-6"><span className="grid h-9 w-9 place-items-center rounded-lg bg-amber-100 font-bold text-amber-700">03</span><h2 className="mt-4 font-bold text-aic-dark">Representative evidence</h2><p className="mt-2 text-sm leading-6 text-aic-muted">Survey weights support national and subnational estimates; upper-tail winsorization limits extreme-value sensitivity.</p></article>
          </section>

          <section className="card p-6 sm:p-8">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between"><div><p className="section-label">Integrated catalog</p><h2 className="mt-2 text-2xl font-bold text-aic-dark">Consumption datasets</h2><p className="mt-1 text-sm text-aic-muted">{datasets.length} of {catalog.total_dataset_count} datasets shown</p></div><div className="grid gap-3 sm:grid-cols-3"><input className="input-field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search country or wave" aria-label="Search datasets"/><select className="input-field" value={country} onChange={(event) => setCountry(event.target.value)} aria-label="Filter by country"><option value="all">All countries</option>{catalog.countries.map((item) => <option key={item} value={item}>{item}</option>)}</select><select className="input-field" value={survey} onChange={(event) => setSurvey(event.target.value)} aria-label="Filter by survey"><option value="all">All surveys</option>{catalog.surveys.map((item) => <option key={item} value={item}>{item}</option>)}</select></div></div>
            <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Country</th><th className="px-4 py-3">Survey</th><th className="px-4 py-3">Wave</th><th className="px-4 py-3">Years</th><th className="px-4 py-3">Size</th><th className="px-4 py-3">Source</th></tr></thead><tbody className="divide-y divide-slate-100">{datasets.map((item) => <tr key={item.id} className="hover:bg-slate-50"><td className="px-4 py-3"><span className="font-semibold text-aic-dark">{item.country}</span><span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-500">{item.country_iso3}</span></td><td className="px-4 py-3 text-slate-600">{item.survey}</td><td className="px-4 py-3 text-slate-600">{item.wave}</td><td className="px-4 py-3 text-slate-600">{item.years}</td><td className="px-4 py-3 text-slate-500">{formatSize(item.size_bytes)}</td><td className="px-4 py-3"><a href={item.download_url} target="_blank" rel="noreferrer" className="font-semibold text-aic-green hover:underline">View authoritative file ↗</a></td></tr>)}</tbody></table></div>
            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><strong className="block">Usage terms require verification</strong><span className="mt-1 block text-xs leading-5">{catalog.license_notice} AIC does not claim ownership or redistribute these files under a new license.</span></div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
            <article className="card p-6 sm:p-8"><p className="section-label">Methodology record</p><h2 className="mt-2 text-2xl font-bold text-aic-dark">How consumption is constructed</h2><dl className="mt-6 divide-y divide-slate-100 text-sm"><div className="py-4"><dt className="font-semibold text-aic-dark">Unit of analysis</dt><dd className="mt-1 leading-6 text-aic-muted">{catalog.methodology.unit_of_analysis}</dd></div><div className="py-4"><dt className="font-semibold text-aic-dark">Valuation</dt><dd className="mt-1 leading-6 text-aic-muted">{catalog.methodology.valuation}</dd></div><div className="py-4"><dt className="font-semibold text-aic-dark">Annualization</dt><dd className="mt-1 leading-6 text-aic-muted">{catalog.methodology.annualization}</dd></div><div className="py-4"><dt className="font-semibold text-aic-dark">Currency</dt><dd className="mt-1 leading-6 text-aic-muted">{catalog.methodology.currency}</dd></div><div className="py-4"><dt className="font-semibold text-aic-dark">Outliers and weights</dt><dd className="mt-1 leading-6 text-aic-muted">{catalog.methodology.outliers} {catalog.methodology.weights}</dd></div></dl></article>
            <aside className="rounded-2xl bg-aic-dark p-6 text-white sm:p-8"><p className="text-xs font-bold uppercase tracking-widest text-emerald-300">Research safeguards</p><h2 className="mt-2 text-xl font-bold">Interpret comparability carefully</h2><ul className="mt-6 space-y-4 text-sm leading-6 text-slate-300">{catalog.methodology.safeguards.map((item) => <li key={item} className="flex gap-3"><span className="text-amber-300">◆</span><span>{item}</span></li>)}</ul><div className="mt-8 flex flex-col gap-3"><Link href="/analysis-lab" className="btn-primary">Open Analysis Lab</Link><a href={catalog.repository} target="_blank" rel="noreferrer" className="rounded-xl border border-white/20 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-white/10">Review source repository ↗</a></div><p className="mt-5 text-xs text-slate-500">Source commit: {catalog.source_commit.slice(0, 12)}</p></aside>
          </section>
        </>}
      </div>
    </main>
  );
}
