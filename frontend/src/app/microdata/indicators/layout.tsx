import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "African Agricultural Indicators — LSMS-ISA Estimates",
  description:
    "Explore 150+ openly-licensed agricultural development indicators for Ethiopia, Malawi, Nigeria, Tanzania and Uganda across 27 LSMS-ISA survey waves — fertilizer and improved-seed adoption, crop yields, livestock, gender equality and income — as interactive multi-country time series.",
  keywords: [
    "LSMS-ISA indicators", "African agriculture data", "fertilizer adoption Africa",
    "crop yields Ethiopia Nigeria Tanzania Uganda Malawi", "agricultural development indicators",
    "EPAR agricultural indicators", "smallholder farming statistics Africa", "food security data",
  ],
  alternates: { canonical: "/microdata/indicators" },
  openGraph: {
    title: "African Agricultural Indicators — LSMS-ISA Estimates",
    description:
      "Interactive multi-country time series of 150+ agricultural indicators across five African countries and 27 LSMS-ISA survey waves.",
    url: "/microdata/indicators",
    type: "website",
  },
};

const DATASET_JSONLD = {
  "@context": "https://schema.org",
  "@type": "Dataset",
  name: "African Agricultural Development Indicators (LSMS-ISA)",
  description:
    "Cross-country agricultural development indicator estimates constructed by EPAR from World Bank LSMS-ISA surveys, covering Ethiopia, Malawi, Nigeria, Tanzania and Uganda across 27 survey waves and 150+ indicators.",
  url: "https://aic.hyrin.org/microdata/indicators",
  creator: { "@type": "Organization", name: "Evans School Policy Analysis & Research (EPAR)" },
  publisher: { "@type": "Organization", name: "African Intelligence Cloud" },
  license: "https://github.com/EvansSchoolPolicyAnalysisAndResearch/LSMS-Data-Dissemination",
  isAccessibleForFree: true,
  spatialCoverage: {
    "@type": "Place",
    name: "Ethiopia, Malawi, Nigeria, Tanzania, Uganda",
  },
  temporalCoverage: "2008/2023",
  variableMeasured: [
    "Proportion of plot managers using inorganic fertilizer",
    "Proportion of plot managers using improved seed",
    "Crop yield", "Livestock holdings (Tropical Livestock Units)",
    "Proportion of rural households engaged in agriculture", "Gender equality in decision-making",
  ],
  keywords: "LSMS-ISA, agriculture, Africa, fertilizer, crop yield, livestock, food security, EPAR",
};

export default function AgIndicatorsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(DATASET_JSONLD) }}
      />
      {children}
    </>
  );
}
