import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AIC Intelligence — Ask Your African Survey Data in Plain Language",
  description:
    "Type a question about poverty, agriculture, diversification or spatial patterns and AIC Intelligence auto-cleans the data and runs the right analysis on African household surveys, with an AI policy brief.",
  alternates: { canonical: "/microdata/intelligence" },
  openGraph: { title: "AIC Intelligence — Ask Your African Survey Data in Plain Language", description: "Type a question about poverty, agriculture, diversification or spatial patterns and AIC Intelligence auto-cleans the data and runs the right analysis on African household surveys, with an AI policy brief.", url: "/microdata/intelligence", type: "website" },
};

export default function AICIntelligenceLayout({ children }: { children: React.ReactNode }) {
  return children;
}
