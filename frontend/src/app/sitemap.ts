import type { MetadataRoute } from "next";

const SITE_URL = "https://aic.hyrin.org";

// Only publicly crawlable routes (must stay in sync with AuthGuard's
// PUBLIC_PATHS) — listing login-gated pages here would feed Google URLs it
// can never render, hurting crawl budget and index quality.
const ROUTES = [
  "",
  "/about",
  "/dashboard",
  "/sdg",
  "/surveys",
  "/health",
  "/search",
  "/research",
  "/docs",
];

export default function sitemap(): MetadataRoute.Sitemap {
  return ROUTES.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified: new Date(),
  }));
}
