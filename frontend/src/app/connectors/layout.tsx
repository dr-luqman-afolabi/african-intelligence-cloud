import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Data Connectors — World Bank, DHS, LSMS & African Statistics",
  description:
    "Connect to open African data sources — World Bank, DHS, LSMS-ISA, IPUMS, Afrobarometer and national statistical offices — for macroeconomic and household survey intelligence.",
  alternates: { canonical: "/connectors" },
  openGraph: { title: "Data Connectors — World Bank, DHS, LSMS & African Statistics", description: "Connect to open African data sources — World Bank, DHS, LSMS-ISA, IPUMS, Afrobarometer and national statistical offices — for macroeconomic and household survey intelligence.", url: "/connectors", type: "website" },
};

export default function ConnectorsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
