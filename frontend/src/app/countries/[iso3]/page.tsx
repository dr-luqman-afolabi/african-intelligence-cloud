import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Country, MacroDataResponse, MacroDataPoint } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";

/** Headline indicators surfaced as cards, in the order a reader expects. */
const HEADLINE = [
  "NY.GDP.MKTP.CD",
  "NY.GDP.MKTP.KD.ZG",
  "FP.CPI.TOTL.ZG",
  "SP.POP.TOTL",
  "SI.POV.DDAY",
  "SL.UEM.TOTL.ZS",
];

async function getCountries(): Promise<Country[]> {
  return serverFetch<Country[]>("/countries", { fallback: [] });
}

async function getCountry(iso3: string): Promise<Country | null> {
  const all = await getCountries();
  return all.find((c) => c.iso3.toUpperCase() === iso3.toUpperCase()) ?? null;
}

/** Pre-render every country at build time — these are the indexable pages. */
export async function generateStaticParams() {
  const countries = await getCountries();
  return countries.map((c) => ({ iso3: c.iso3.toLowerCase() }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ iso3: string }>;
}): Promise<Metadata> {
  const { iso3 } = await params;
  const country = await getCountry(iso3);
  if (!country) return { title: "Country not found" };

  const title = `${country.name} — Economic & Development Data`;
  const description = `GDP, inflation, poverty, trade, debt, population, health and education indicators for ${country.name}. Harmonized data and analysis tools from African Intelligence Cloud.`;
  return {
    title,
    description,
    alternates: { canonical: `/countries/${country.iso3.toLowerCase()}` },
    openGraph: { title, description, url: `/countries/${country.iso3.toLowerCase()}` },
  };
}

/** Latest observation per indicator, plus the span of years available. */
function summarise(data: MacroDataPoint[]) {
  const byCode = new Map<string, MacroDataPoint[]>();
  for (const p of data) {
    if (p.value === null || p.value === undefined) continue;
    const list = byCode.get(p.indicator_code) ?? [];
    list.push(p);
    byCode.set(p.indicator_code, list);
  }
  return Array.from(byCode.entries())
    .map(([code, points]) => {
      const sorted = [...points].sort((a, b) => b.year - a.year);
      const years = points.map((p) => p.year);
      return {
        code,
        name: sorted[0].indicator_name,
        unit: sorted[0].unit || "",
        latest: sorted[0],
        from: Math.min(...years),
        to: Math.max(...years),
        count: points.length,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

function formatValue(value: number, code: string, unit: string) {
  const isPercent = unit === "%" || code.endsWith(".ZS") || code.endsWith(".ZG");
  if (isPercent) return `${value.toFixed(1)}%`;
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return value.toFixed(Math.abs(value) < 10 ? 2 : 1);
}

export default async function CountryPage({ params }: { params: Promise<{ iso3: string }> }) {
  const { iso3 } = await params;
  const country = await getCountry(iso3);
  if (!country) notFound();

  const macro = await serverFetch<MacroDataResponse>(
    `/macro-data?country=${country.iso3}`,
    { fallback: { country_iso3: country.iso3, country_name: country.name, data: [] } },
  );

  const indicators = summarise(macro.data ?? []);
  const headline = HEADLINE.map((c) => indicators.find((i) => i.code === c)).filter(
    (x): x is NonNullable<typeof x> => !!x,
  );
  const yearsCovered = indicators.length
    ? { from: Math.min(...indicators.map((i) => i.from)), to: Math.max(...indicators.map((i) => i.to)) }
    : null;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${country.name} economic and development indicators`,
    description: `Macroeconomic and development time series for ${country.name}, harmonized by African Intelligence Cloud.`,
    url: `https://aic.hyrin.org/countries/${country.iso3.toLowerCase()}`,
    spatialCoverage: { "@type": "Place", name: country.name },
    ...(yearsCovered ? { temporalCoverage: `${yearsCovered.from}/${yearsCovered.to}` } : {}),
    variableMeasured: indicators.slice(0, 30).map((i) => i.name),
    creator: { "@type": "Organization", name: "African Intelligence Cloud" },
    isAccessibleForFree: true,
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <nav className="text-sm text-slate-400">
        <Link href="/countries" className="hover:text-aic-green">
          Countries
        </Link>{" "}
        / <span className="text-slate-600">{country.name}</span>
      </nav>

      <h1 className="mt-3 text-4xl font-bold tracking-tight text-aic-dark">
        {country.name} — Data &amp; Economic Intelligence
      </h1>
      <p className="mt-2 text-sm text-slate-500">
        {country.region}
        {country.income_group ? ` · ${country.income_group}` : ""} · ISO {country.iso3}
        {yearsCovered ? ` · data ${yearsCovered.from}–${yearsCovered.to}` : ""}
      </p>

      {indicators.length === 0 ? (
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No macroeconomic series are currently available for {country.name}. Coverage depends on
          source-data availability.
        </div>
      ) : (
        <>
          {headline.length > 0 && (
            <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
              {headline.map((i) => (
                <div key={i.code} className="card p-5">
                  <p className="text-xs uppercase tracking-wide text-slate-400">{i.name}</p>
                  <p className="mt-1 text-2xl font-bold text-aic-dark">
                    {formatValue(i.latest.value, i.code, i.unit)}
                  </p>
                  <p className="text-xs text-slate-400">{i.latest.year}</p>
                </div>
              ))}
            </div>
          )}

          <section className="mt-12">
            <h2 className="text-2xl font-bold text-aic-dark">
              All indicators tracked for {country.name}
            </h2>
            <p className="mt-2 text-sm text-aic-muted">
              {indicators.length} indicators · {macro.data.length.toLocaleString()} observations.
            </p>
            <div className="mt-5 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-2 pr-4 font-medium">Indicator</th>
                    <th className="py-2 pr-4 font-medium">Latest</th>
                    <th className="py-2 pr-4 font-medium">Year</th>
                    <th className="py-2 pr-4 font-medium">Coverage</th>
                  </tr>
                </thead>
                <tbody>
                  {indicators.map((i) => (
                    <tr key={i.code} className="border-b border-slate-100">
                      <td className="py-2 pr-4 text-slate-700">{i.name}</td>
                      <td className="py-2 pr-4 font-medium text-aic-dark">
                        {formatValue(i.latest.value, i.code, i.unit)}
                      </td>
                      <td className="py-2 pr-4 text-slate-500">{i.latest.year}</td>
                      <td className="py-2 pr-4 text-slate-400">
                        {i.from}–{i.to}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-aic-dark">Analyse {country.name}</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Link href="/dashboard" className="card card-hover p-5">
            <p className="font-semibold text-aic-green">Macro Dashboard →</p>
            <p className="mt-1 text-sm text-slate-500">
              Chart and compare {country.name}&apos;s indicators over time.
            </p>
          </Link>
          <Link href="/microdata" className="card card-hover p-5">
            <p className="font-semibold text-aic-green">Microdata Studio →</p>
            <p className="mt-1 text-sm text-slate-500">
              Run poverty, inequality and welfare analysis on household surveys.
            </p>
          </Link>
          <Link href="/sdg" className="card card-hover p-5">
            <p className="font-semibold text-aic-green">SDG Tracker →</p>
            <p className="mt-1 text-sm text-slate-500">
              Progress against all 17 Sustainable Development Goals.
            </p>
          </Link>
          <Link href="/surveys" className="card card-hover p-5">
            <p className="font-semibold text-aic-green">Survey Catalogue →</p>
            <p className="mt-1 text-sm text-slate-500">
              Household and census microdata series covering {country.name}.
            </p>
          </Link>
        </div>
      </section>

      <p className="mt-10 text-xs text-slate-400">
        Source: World Bank Open Data, harmonized by African Intelligence Cloud. Coverage varies by
        indicator and year subject to source-data availability.
      </p>
    </div>
  );
}
