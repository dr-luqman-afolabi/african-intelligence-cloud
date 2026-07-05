import type { MetadataRoute } from "next";

const SITE_URL = "https://aic.hyrin.org";

const ROUTES = [
  "",
  "/about",
  "/dashboard",
  "/datasets",
  "/surveys",
  "/connectors",
  "/health",
  "/search",
  "/sdg",
  "/research",
  "/docs",
];

export default function sitemap(): MetadataRoute.Sitemap {
  return ROUTES.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified: new Date(),
  }));
}
