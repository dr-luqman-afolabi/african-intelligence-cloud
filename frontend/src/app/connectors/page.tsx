import { serverFetch } from "@/lib/serverApi";
import ConnectorExplorer, { type ConnectorListItem } from "./ConnectorExplorer";

// Server component: the connector registry is fetched here so all catalogued
// sources appear in the initial HTML. Search, filtering, health checks and sync
// actions remain client-side inside ConnectorExplorer.
export default async function ConnectorsPage() {
  const connectors = await serverFetch<ConnectorListItem[]>("/connectors", { fallback: [] });

  if (connectors.length === 0) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-aic-dark mb-1">Data Connectors</h1>
        <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-amber-800 text-sm">
          Connectors are temporarily unavailable. Please try again shortly.
        </div>
      </div>
    );
  }

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "AIC Data Connectors",
    description:
      "Catalogued African and international statistical data sources connected to the African Intelligence Cloud platform.",
    numberOfItems: connectors.length,
    itemListElement: connectors.slice(0, 100).map((c, i) => ({
      "@type": "ListItem",
      position: i + 1,
      item: {
        "@type": "DataCatalog",
        name: c.source_name,
        description: c.source_type,
        ...(c.data_owner ? { provider: { "@type": "Organization", name: c.data_owner } } : {}),
      },
    })),
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <ConnectorExplorer connectors={connectors} />
    </>
  );
}
