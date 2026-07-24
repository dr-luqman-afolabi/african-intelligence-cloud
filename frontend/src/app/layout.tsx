import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import AuthGuard from "@/components/AuthGuard";

const SITE_URL = "https://aic.hyrin.org";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "African Intelligence Cloud",
    template: "%s | African Intelligence Cloud",
  },
  description:
    "Africa's data and policy intelligence platform: LSMS & household-survey microdata, poverty and inequality analysis, agricultural productivity, spatial poverty maps, World Bank & DHS indicators, SDG tracking, and AI-generated policy briefs across all 54 African countries.",
  applicationName: "African Intelligence Cloud",
  category: "Data & Analytics",
  keywords: [
    "Africa data", "African economic data", "LSMS microdata", "household survey Africa",
    "poverty analysis Africa", "inequality Gini Africa", "agricultural productivity Africa",
    "spatial poverty maps", "GIS poverty Africa", "DHS data", "World Bank indicators Africa",
    "SDG Africa", "policy brief Africa", "Nigeria data", "Kenya data", "Ethiopia data",
    "Tanzania data", "Uganda data", "Ghana data", "Rwanda data", "South Africa data",
    "African development statistics", "microdata analytics", "poverty headcount", "food security Africa",
  ],
  authors: [{ name: "African Intelligence Cloud" }],
  creator: "African Intelligence Cloud",
  publisher: "African Intelligence Cloud",
  robots: { index: true, follow: true, googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 } },
  openGraph: {
    title: "African Intelligence Cloud",
    description: "Macroeconomic data, analytics, and policy intelligence for Africa.",
    url: SITE_URL,
    siteName: "African Intelligence Cloud",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "African Intelligence Cloud",
    description: "Macroeconomic data, analytics, and policy intelligence for Africa.",
  },
  alternates: {
    canonical: "/",
    languages: {
      "en": "/",
      "en-NG": "/", "en-KE": "/", "en-ZA": "/", "en-GH": "/",
      "en-UG": "/", "en-TZ": "/", "en-RW": "/", "en-ET": "/",
      "fr": "/", "x-default": "/",
    },
  },
  other: {
    "geo.region": "Africa",
    "geo.placename": "Africa",
    "distribution": "global",
    "coverage": "Africa",
    "target": "all",
  },
};

// Structured data so Google understands the site as an organization + a
// searchable dataset platform (eligible for richer results).
const JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      name: "African Intelligence Cloud",
      url: SITE_URL,
      description:
        "Data, analytics and policy-intelligence platform for all 54 African countries — LSMS microdata, poverty & agriculture analytics, spatial poverty maps, and AI policy briefs.",
      areaServed: { "@type": "Place", name: "Africa" },
      knowsAbout: ["Poverty analysis", "LSMS microdata", "Agricultural productivity", "Spatial poverty mapping", "SDG indicators", "African economic development"],
      email: "aluqman@hyrin.org",
      sameAs: ["https://hyrin.org"],
      founder: {
        "@type": "Person",
        name: "Dr. Luqman O. Afolabi",
        jobTitle: "Founder & Director",
        email: "aluqman@hyrin.org",
        sameAs: ["https://hyrin.org/about.html"],
      },
      member: [
        { "@type": "Person", name: "Dr. Yusuf Hammed Agboola", jobTitle: "Lead Development Economist", sameAs: ["https://hyrin.org/about.html"] },
        { "@type": "Person", name: "Dr. Abdulmalik O. Salau", jobTitle: "Director of Financial Governance", sameAs: ["https://hyrin.org/about.html"] },
        { "@type": "Person", name: "Azeezat Gbadamosi", jobTitle: "Public Health & Impact Monitoring", sameAs: ["https://hyrin.org/about.html"] },
        { "@type": "Person", name: "Dr. Toluwalope Ogunro", jobTitle: "Senior Advisor, Environmental Health", sameAs: ["https://hyrin.org/about.html"] },
      ],
      parentOrganization: {
        "@type": "NGO",
        name: "H.Y.R.I.N. — Holistic Youth Resilience & Innovation Network",
        url: "https://hyrin.org",
        identifier: "CAC RC 8729824",
      },
    },
    {
      "@type": "DataCatalog",
      name: "African Intelligence Cloud Data Catalog",
      url: `${SITE_URL}/datasets`,
      description:
        "Catalog of LSMS/household-survey microdata, macroeconomic indicators and derived poverty, inequality, agriculture and diversification analytics for African countries.",
      spatialCoverage: { "@type": "Place", name: "Africa" },
      keywords: "LSMS, household survey, poverty, inequality, agriculture, DHS, MICS, Afrobarometer, SDG, Africa",
    },
    {
      "@type": "WebSite",
      name: "African Intelligence Cloud",
      url: SITE_URL,
      potentialAction: {
        "@type": "SearchAction",
        target: `${SITE_URL}/search?q={search_term_string}`,
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "Dataset",
      name: "African Macroeconomic Indicators",
      description:
        "Historical macroeconomic, social, and environmental indicators for 54 African countries, sourced from World Bank Open Data, WHO, FAO, and other public sources.",
      url: `${SITE_URL}/dashboard`,
      license: "https://creativecommons.org/licenses/by/4.0/",
      creator: { "@type": "Organization", name: "African Intelligence Cloud" },
      spatialCoverage: "Africa",
    },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
        />
        <Navbar />
        <main className="min-h-[calc(100vh-4rem)]">
          <AuthGuard>{children}</AuthGuard>
        </main>
        <Footer />
      </body>
    </html>
  );
}
