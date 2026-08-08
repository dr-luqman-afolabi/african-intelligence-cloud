import type { SurveyEntry } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";
import PageHeader from "@/components/ui/PageHeader";
import SurveyCatalog from "./SurveyCatalog";

// Server component: the catalogue is fetched here so every survey is present in
// the initial HTML for crawlers. Only the topic filter is client-side.
export default async function SurveysPage() {
  const surveys = await serverFetch<SurveyEntry[]>("/surveys", { fallback: [] });

  // Surface the catalogue to search engines as a structured dataset list.
  const jsonLd = surveys.length
    ? {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: "African Survey Catalogue",
        numberOfItems: surveys.length,
        itemListElement: surveys.slice(0, 100).map((s, i) => ({
          "@type": "ListItem",
          position: i + 1,
          item: {
            "@type": "Dataset",
            name: s.title,
            description: `${s.series} household survey${s.country_iso3 ? ` for ${s.country_iso3}` : ""}.`,
            license: s.requires_approval
              ? "Restricted access — registration required"
              : "Open access — registration not required",
            ...(s.access_url ? { url: s.access_url } : {}),
            ...(s.country_iso3 ? { spatialCoverage: s.country_iso3 } : {}),
          },
        })),
      }
    : null;

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      )}

      <PageHeader
        eyebrow="Survey catalog"
        title="Microdata & Survey Catalog"
        description="Household, health, and census microdata series available for research (DHS, LSMS, IPUMS, MICS, and more)."
      />

      {surveys.length === 0 ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-amber-800 text-sm">
          The survey catalogue is temporarily unavailable. Please try again shortly.
        </div>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {surveys.length} survey series catalogued across Africa.
          </p>
          <SurveyCatalog surveys={surveys} />
        </>
      )}
    </div>
  );
}
