import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Search African Data",
  description:
    "Semantic search across African macroeconomic indicators, survey catalogues, and research datasets.",
  alternates: { canonical: "/search" },
};

export default function SearchLayout({ children }: { children: React.ReactNode }) {
  return children;
}
