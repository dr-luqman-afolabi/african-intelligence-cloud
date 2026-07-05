import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  metadataBase: new URL("https://aic-frontend-87872864140.africa-south1.run.app"),
  title: {
    default: "African Intelligence Cloud",
    template: "%s | African Intelligence Cloud",
  },
  description: "Macroeconomic data, analytics, and policy intelligence for Africa. Powered by World Bank data across 54 countries, with AI-enhanced insights, SDG tracking, and microdata.",
  keywords: ["Africa data", "World Bank indicators", "SDG tracking", "African macroeconomic data", "policy intelligence", "African Intelligence Cloud"],
  authors: [{ name: "Dr. Luqman Afolabi" }],
  openGraph: {
    title: "African Intelligence Cloud",
    description: "Macroeconomic data, analytics, and policy intelligence for Africa across 54 countries.",
    type: "website",
    siteName: "African Intelligence Cloud",
  },
  twitter: {
    card: "summary_large_image",
    title: "African Intelligence Cloud",
    description: "Macroeconomic data, analytics, and policy intelligence for Africa across 54 countries.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
