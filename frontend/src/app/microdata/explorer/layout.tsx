import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Spatial Explorer — African Poverty & Agriculture Choropleth Maps",
  description:
    "Interactive choropleth maps with Moran's I and LISA hotspot analysis for poverty, agriculture and diversification across African administrative regions, powered by household survey microdata.",
  alternates: { canonical: "/microdata/explorer" },
  openGraph: { title: "Spatial Explorer — African Poverty & Agriculture Choropleth Maps", description: "Interactive choropleth maps with Moran's I and LISA hotspot analysis for poverty, agriculture and diversification across African administrative regions, powered by household survey microdata.", url: "/microdata/explorer", type: "website" },
};

export default function SpatialExplorerLayout({ children }: { children: React.ReactNode }) {
  return children;
}
