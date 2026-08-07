import type { Metadata } from "next";
import Link from "next/link";
import type { SurveyEntry } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";
import type { ConnectorListItem } from "../connectors/ConnectorExplorer";

export const metadata: Metadata = {
  title: "Data Catalogue — African Statistical Sources & Survey Series",
  description:
    "The data behind African Intelligence Cloud: catalogued statistical sources including World Bank, IMF, WHO, FAO, UN and national statistical offices, plus African household survey series — LSMS, DHS, MICS, EICV and more.",
  alternates: { canonical: "/data" },
};

/** Group sources into categories a reader recognises, rather than by internal
 *  registry tier. Matching is on the source id/name because the registry has no
 *  category field — kept here so the grouping is visible and correctable. */
const CATEGORIES: { title: string; blurb: string; match: (c: ConnectorListItem) => boolean }[] = [
  {
    title: "International & multilateral",
    blurb: "Global statistical agencies publishing comparable cross-country series.",
    match: (c) =>
      /world_bank|imf|un_|unesco|who|fao|ilo|wto|comtrade|unctad|oecd|undp|unicef/i.test(
        c.source_id,
      ),
  },
  {
    title: "Household & census microdata",
    blurb: "Survey programmes producing household-level data for poverty, health and living standards.",
    match: (c) => /dhs|lsms|mics|ipums|afrobarometer|microdata|nada|ihsn|unps|eicv/i.test(c.source_id),
  },
  {
    title: "Geospatial & environment",
    blurb: "Boundaries, climate, rainfall and earth-observation sources behind the spatial analysis.",
    match: (c) => /hdx|gadm|geo|chirps|nasa|climate|carbon|osm|overpass|nighttime|spatial/i.test(c.source_id),
  },
  {
    title: "Regional & national",
    blurb: "African regional bodies and national statistical offices.",
    match: (c) => /afdb|nisr|nbs|knbs|stats_|_rwanda|_nigeria|_kenya|_tanzania|_south_africa|au_/i.test(c.source_id),
  },
];

export default async function DataPage() {
  const [connectors, surveys] = await Promise.all([
    serverFetch<ConnectorListItem[]>("/connectors", { fallback: [] }),
    serverFetch<SurveyEntry[]>("/surveys", { fallback: [] }),
  ]);

  const grouped = CATEGORIES.map((cat) => ({
    ...cat,
    items: connectors.filter(cat.match),
  })).filter((g) => g.items.length > 0);

  const categorised = new Set(grouped.flatMap((g) => g.items.map((i) => i.source_id)));
  const other = connectors.filter((c) => !categorised.has(c.source_id));

  const liveCount = connectors.filter((c) => c.connector_status === "live").length;

  const jsonLd = connectors.length
    ? {
        "@context": "https://schema.org",
        "@type": "DataCatalog",
        name: "African Intelligence Cloud Data Catalogue",
        description:
          "Statistical sources and African household survey series integrated into the African Intelligence Cloud platform.",
        url: "https://aic.hyrin.org/data",
        provider: { "@type": "Organization", name: "African Intelligence Cloud" },
        dataset: connectors.slice(0, 60).map((c) => ({
          "@type": "Dataset",
          name: c.source_name,
          description: c.source_type,
          ...(c.data_owner ? { creator: { "@type": "Organization", name: c.data_owner } } : {}),
        })),
      }
    : null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      )}

      <p className="section-label">Data catalogue</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">
        The data behind the platform
      </h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        AIC does not republish data under its own name. Every series carries the licence and
        attribution of its original provider, and each source below records its access conditions
        and update frequency. Coverage varies by country and year according to what the source
        actually publishes.
      </p>

      {connectors.length === 0 ? (
        <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          The catalogue is temporarily unavailable. Please try again shortly.
        </div>
      ) : (
        <>
          <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="card px-4 py-5 text-center">
              <p className="text-2xl font-bold text-aic-dark">{connectors.length}</p>
              <p className="mt-1 text-xs text-slate-500">Catalogued sources</p>
            </div>
            <div className="card px-4 py-5 text-center">
              <p className="text-2xl font-bold text-aic-dark">{liveCount}</p>
              <p className="mt-1 text-xs text-slate-500">Live connectors</p>
            </div>
            <div className="card px-4 py-5 text-center">
              <p className="text-2xl font-bold text-aic-dark">{surveys.length}</p>
              <p className="mt-1 text-xs text-slate-500">Survey series</p>
            </div>
            <div className="card px-4 py-5 text-center">
              <p className="text-2xl font-bold text-aic-dark">54</p>
              <p className="mt-1 text-xs text-slate-500">Countries covered</p>
            </div>
          </div>

          <div className="mt-12 space-y-12">
            {grouped.map((g) => (
              <section key={g.title}>
                <h2 className="text-2xl font-bold text-aic-dark">{g.title}</h2>
                <p className="mt-1 text-sm text-aic-muted">{g.blurb}</p>
                <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {g.items.map((c) => (
                    <div key={c.source_id} className="card p-5">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-semibold text-aic-dark">{c.source_name}</h3>
                        {c.connector_status === "live" && (
                          <span className="badge shrink-0 bg-aic-green/10 text-aic-green">Live</span>
                        )}
                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{c.source_type}</p>
                      <p className="mt-2 text-xs text-slate-400">
                        Licence {c.license_category} · {c.update_frequency}
                        {c.requires_approval ? " · registration required" : ""}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            ))}

            {other.length > 0 && (
              <section>
                <h2 className="text-2xl font-bold text-aic-dark">Other sources</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {other.map((c) => (
                    <span key={c.source_id} className="badge bg-slate-100 text-slate-600">
                      {c.source_name}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>

          <section className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Link href="/connectors" className="card card-hover p-6">
              <h3 className="font-semibold text-aic-green">Source health &amp; detail →</h3>
              <p className="mt-1.5 text-sm text-slate-500">
                Per-source status, licence terms and sync history.
              </p>
            </Link>
            <Link href="/surveys" className="card card-hover p-6">
              <h3 className="font-semibold text-aic-green">Survey catalogue →</h3>
              <p className="mt-1.5 text-sm text-slate-500">
                Household and census series with access conditions and documentation.
              </p>
            </Link>
            <Link href="/countries" className="card card-hover p-6">
              <h3 className="font-semibold text-aic-green">Browse by country →</h3>
              <p className="mt-1.5 text-sm text-slate-500">
                What data exists for each of the 54 African countries.
              </p>
            </Link>
          </section>

          <p className="mt-10 text-xs text-slate-400">
            Licensing, attribution and how uploaded microdata is handled are set out in{" "}
            <Link href="/governance/data-governance" className="text-aic-green underline underline-offset-4">
              data governance
            </Link>
            .
          </p>
        </>
      )}
    </div>
  );
}
