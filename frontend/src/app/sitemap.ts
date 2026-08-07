import type { MetadataRoute } from "next";
import type { Country } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";
import { SOLUTIONS } from "@/lib/solutions";
import { GOVERNANCE } from "@/lib/governance";

const SITE_URL = "https://aic.hyrin.org";

// Only publicly crawlable routes (must stay in sync with AuthGuard's
// PUBLIC_PATHS) — listing login-gated pages here would feed Google URLs it
// can never render, hurting crawl budget and index quality. `priority` and
// `changeFrequency` hint Google toward the pages we most want indexed.
type Route = {
  path: string;
  priority: number;
  changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"];
};

const ROUTES: Route[] = [
  { path: "", priority: 1.0, changeFrequency: "daily" },
  { path: "/about", priority: 0.9, changeFrequency: "monthly" },
  { path: "/dashboard", priority: 0.9, changeFrequency: "daily" },
  { path: "/microdata", priority: 0.9, changeFrequency: "weekly" },
  { path: "/countries", priority: 0.9, changeFrequency: "weekly" },
  { path: "/solutions", priority: 0.9, changeFrequency: "monthly" },
  { path: "/partners", priority: 0.8, changeFrequency: "monthly" },
  { path: "/governance", priority: 0.6, changeFrequency: "yearly" },
  { path: "/sdg", priority: 0.8, changeFrequency: "weekly" },
  { path: "/research", priority: 0.8, changeFrequency: "weekly" },
  { path: "/surveys", priority: 0.7, changeFrequency: "weekly" },
  { path: "/microdata/indicators", priority: 0.7, changeFrequency: "weekly" },
  { path: "/harveststat", priority: 0.7, changeFrequency: "weekly" },
  { path: "/forecast", priority: 0.7, changeFrequency: "weekly" },
  { path: "/connectors", priority: 0.6, changeFrequency: "weekly" },
  { path: "/health", priority: 0.5, changeFrequency: "weekly" },
  { path: "/search", priority: 0.5, changeFrequency: "monthly" },
  { path: "/docs", priority: 0.5, changeFrequency: "monthly" },
  { path: "/contact", priority: 0.6, changeFrequency: "yearly" },
  { path: "/privacy", priority: 0.3, changeFrequency: "yearly" },
  { path: "/terms", priority: 0.3, changeFrequency: "yearly" },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const lastModified = new Date();

  const base = ROUTES.map(({ path, priority, changeFrequency }) => ({
    url: `${SITE_URL}${path}`,
    lastModified,
    changeFrequency,
    priority,
  }));

  // One entry per country page. Generated from the live list rather than a
  // hardcoded array so the sitemap can't drift from what actually renders.
  const countries = await serverFetch<Country[]>("/countries", { fallback: [] });
  const countryRoutes = countries.map((c) => ({
    url: `${SITE_URL}/countries/${c.iso3.toLowerCase()}`,
    lastModified,
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }));

  const solutionRoutes = SOLUTIONS.map((s) => ({
    url: `${SITE_URL}/solutions/${s.slug}`,
    lastModified,
    changeFrequency: "monthly" as const,
    priority: 0.8,
  }));

  const governanceRoutes = GOVERNANCE.map((d) => ({
    url: `${SITE_URL}/governance/${d.slug}`,
    lastModified,
    changeFrequency: "yearly" as const,
    priority: 0.5,
  }));

  return [...base, ...countryRoutes, ...solutionRoutes, ...governanceRoutes];
}
