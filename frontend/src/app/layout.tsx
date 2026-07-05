import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  );
}
