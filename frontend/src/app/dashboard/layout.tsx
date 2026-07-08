import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Macro Dashboard — African Economic Indicators",
  description:
    "Interactive macroeconomic dashboard for 54 African countries: GDP, inflation, poverty, health, education, trade, and environment indicators from World Bank Open Data. Compare indicators, zoom time ranges, and generate AI interpretations.",
  alternates: { canonical: "/dashboard" },
  openGraph: {
    title: "African Macro Dashboard",
    description:
      "Explore GDP, inflation, poverty, and 20+ development indicators across all African countries.",
    url: "/dashboard",
  },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
