import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Research Assistant — African Development Research",
  description:
    "AI-assisted research tools for African development studies: literature reviews, theory and method recommendations, research gap identification, and paper search across OpenAlex, Crossref, and more.",
  alternates: { canonical: "/research" },
};

export default function ResearchLayout({ children }: { children: React.ReactNode }) {
  return children;
}
