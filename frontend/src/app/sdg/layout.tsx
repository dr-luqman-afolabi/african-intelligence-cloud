import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SDG Tracker — Sustainable Development Goals in Africa",
  description:
    "Track all 17 Sustainable Development Goals across African countries: country rankings, regional breakdowns, and indicator trends for poverty, health, education, climate, and more.",
  alternates: { canonical: "/sdg" },
  openGraph: {
    title: "Africa SDG Tracker",
    description:
      "Country-level progress on all 17 Sustainable Development Goals across Africa.",
    url: "/sdg",
  },
};

export default function SDGLayout({ children }: { children: React.ReactNode }) {
  return children;
}
