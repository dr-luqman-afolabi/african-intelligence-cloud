import type { Metadata } from "next";
import Link from "next/link";
import type { Country } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";

export const metadata: Metadata = {
  title: "African Countries — Economic & Development Data",
  description:
    "Country-level economic and development intelligence for all 54 African countries: GDP, inflation, poverty, trade, debt, population, health and education indicators.",
  alternates: { canonical: "/countries" },
};

export default async function CountriesPage() {
  const countries = await serverFetch<Country[]>("/countries", { fallback: [] });

  const byRegion = countries.reduce<Record<string, Country[]>>((acc, c) => {
    const key = c.region || "Other";
    (acc[key] ||= []).push(c);
    return acc;
  }, {});
  const regions = Object.keys(byRegion).sort();

  const jsonLd = countries.length
    ? {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: "African countries covered by African Intelligence Cloud",
        numberOfItems: countries.length,
        itemListElement: countries.map((c, i) => ({
          "@type": "ListItem",
          position: i + 1,
          name: c.name,
          url: `https://aic.hyrin.org/countries/${c.iso3.toLowerCase()}`,
        })),
      }
    : null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      )}

      <p className="section-label">Countries</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">
        African Country Intelligence
      </h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        Economic and development data for every African country — GDP, inflation, trade, debt,
        poverty, population, health and education — drawn from World Bank Open Data and harmonized
        for cross-country comparison. Coverage depends on source-data availability per country.
      </p>

      {countries.length === 0 ? (
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Country data is temporarily unavailable. Please try again shortly.
        </div>
      ) : (
        <>
          <p className="mt-6 text-sm text-slate-500">{countries.length} countries covered.</p>
          <div className="mt-8 space-y-10">
            {regions.map((region) => (
              <section key={region}>
                <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500">
                  {region}
                  <span className="ml-2 font-normal normal-case tracking-normal text-slate-400">
                    ({byRegion[region].length})
                  </span>
                </h2>
                <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                  {byRegion[region]
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((c) => (
                      <Link
                        key={c.iso3}
                        href={`/countries/${c.iso3.toLowerCase()}`}
                        className="card card-hover flex items-center justify-between px-4 py-3"
                      >
                        <span className="text-sm font-medium text-aic-dark">{c.name}</span>
                        <span className="text-xs font-semibold text-slate-400">{c.iso3}</span>
                      </Link>
                    ))}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
