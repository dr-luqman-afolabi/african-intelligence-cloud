/**
 * Server-side data fetching for public catalogue pages.
 *
 * These pages were client-rendered, so crawlers saw only the shell — nav,
 * heading and footer — while the actual catalogue arrived later via XHR. That
 * left the most search-relevant content on the site invisible to Google.
 * Fetching here instead puts the real rows in the initial HTML.
 *
 * Uses the native fetch cache rather than the axios client: axios is a browser
 * concern and bypasses Next's caching. `revalidate` keeps pages static and
 * fast while still refreshing as upstream data changes, and a failed upstream
 * call degrades to an empty list so a flaky API renders a thin page instead of
 * a 500.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DEFAULT_REVALIDATE = 3600; // 1 hour

export async function serverFetch<T>(
  path: string,
  { revalidate = DEFAULT_REVALIDATE, fallback }: { revalidate?: number; fallback: T },
): Promise<T> {
  try {
    const res = await fetch(`${API_URL}/api/v1${path}`, {
      next: { revalidate },
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}
