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
    "Macroeconomic data, analytics, and policy intelligence for Africa. Explore World Bank indicators, SDG progress, and AI-enhanced research across African countries.",
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
        "Macroeconomic data, analytics, and policy intelligence platform for all 54 African countries.",
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
