import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "African Crop Statistics — Subnational Yield & Production",
  description:
    "Explore openly-licensed harmonized subnational crop statistics for Africa — area, production and yield by country, region, crop and season from HarvestStat-Africa — as interactive multi-country time series.",
  keywords: [
    "African crop statistics", "subnational crop yield Africa", "maize yield Africa",
    "crop production data Africa", "HarvestStat Africa", "food security crop data",
    "agricultural production statistics", "harmonized crop data",
  ],
  alternates: { canonical: "/harveststat" },
  openGraph: {
    title: "African Crop Statistics — Subnational Yield & Production",
    description:
      "Interactive multi-country time series of subnational crop area, production and yield across Africa.",
    url: "/harveststat",
    type: "website",
  },
};

const DATASET_JSONLD = {
  "@context": "https://schema.org",
  "@type": "Dataset",
  name: "HarvestStat-Africa — Harmonized Subnational Crop Statistics",
  description:
    "Open-access harmonized subnational crop area, production and yield statistics across African countries, administrative regions, crops and seasons.",
  url: "https://aic.hyrin.org/harveststat",
  creator: { "@type": "Organization", name: "HarvestStat" },
  publisher: { "@type": "Organization", name: "African Intelligence Cloud" },
  license: "https://github.com/HarvestStat/HarvestStat-Africa",
  isAccessibleForFree: true,
  spatialCoverage: { "@type": "Place", name: "Africa" },
  variableMeasured: ["Crop area (ha)", "Crop production (t)", "Crop yield (t/ha)"],
  keywords: "crop statistics, yield, production, Africa, food security, HarvestStat, subnational",
};

export default function CropStatsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(DATASET_JSONLD) }} />
      {children}
    </>
  );
}
