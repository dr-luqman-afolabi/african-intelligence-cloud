import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Microdata Analytics Studio — Poverty, Agriculture & Diversification",
  description:
    "Upload household survey microdata and instantly compute poverty (FGT), inequality (Gini), agricultural productivity and livelihood diversification indices for African countries — no code required.",
  alternates: { canonical: "/microdata" },
  openGraph: { title: "Microdata Analytics Studio — Poverty, Agriculture & Diversification", description: "Upload household survey microdata and instantly compute poverty (FGT), inequality (Gini), agricultural productivity and livelihood diversification indices for African countries — no code required.", url: "/microdata", type: "website" },
};

export default function MicrodataLayout({ children }: { children: React.ReactNode }) {
  return children;
}
