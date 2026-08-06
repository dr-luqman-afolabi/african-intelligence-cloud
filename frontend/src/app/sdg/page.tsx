import type { SDGGoal, CountryEntry } from "@/lib/api";
import { serverFetch } from "@/lib/serverApi";
import SDGExplorer from "./SDGExplorer";

const SDG_COLORS = [
  "#e5243b", "#dda63a", "#4c9f38", "#c5192d", "#ff3a21",
  "#26bde2", "#fcc30b", "#a21942", "#fd6925", "#dd1367",
  "#fd9d24", "#bf8b2e", "#3f7e44", "#0a97d9", "#56c02b",
  "#00689d", "#19486a",
];

// Server component: all 17 goals — titles, descriptions and the indicators AIC
// tracks for each — are rendered here so they appear in the initial HTML. The
// chart and goal/country selectors stay interactive in SDGExplorer.
export default async function SDGPage() {
  const [goals, countries] = await Promise.all([
    serverFetch<SDGGoal[]>("/sdg/goals", { fallback: [] }),
    serverFetch<CountryEntry[]>("/countries", { fallback: [] }),
  ]);

  const jsonLd = goals.length
    ? {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: "Sustainable Development Goals tracked across Africa",
        numberOfItems: goals.length,
        itemListElement: goals.map((g) => ({
          "@type": "ListItem",
          position: g.goal_number,
          name: `SDG ${g.goal_number}: ${g.title}`,
          description: g.description,
        })),
      }
    : null;

  return (
    <>
      {jsonLd && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      )}

      {goals.length === 0 ? (
        <div className="max-w-3xl mx-auto px-6 py-16">
          <h1 className="text-3xl font-bold text-aic-dark">SDG Tracker</h1>
          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-amber-800 text-sm">
            SDG data is temporarily unavailable. Please try again shortly.
          </div>
        </div>
      ) : (
        <SDGExplorer goals={goals} countries={countries} />
      )}

      {/* Crawlable reference: the goal catalogue in full, below the explorer.
          This is the substantive text a search engine can index — previously
          the page shipped only a heading and an empty shell. */}
      {goals.length > 0 && (
        <section className="bg-white border-t border-slate-200">
          <div className="mx-auto max-w-5xl px-6 py-14">
            <p className="section-label">Reference</p>
            <h2 className="mt-2 text-3xl font-bold text-aic-dark">
              All 17 Sustainable Development Goals
            </h2>
            <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
              The United Nations Sustainable Development Goals tracked by African Intelligence
              Cloud, with the indicators used to measure progress for each African country where
              source data is available.
            </p>

            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {goals.map((g) => (
                <article key={g.goal_number} className="card p-5">
                  <div className="flex items-start gap-3">
                    <span
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white"
                      style={{ backgroundColor: SDG_COLORS[(g.goal_number - 1) % SDG_COLORS.length] }}
                    >
                      {g.goal_number}
                    </span>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-aic-dark">{g.title}</h3>
                      <p className="mt-1 text-sm leading-relaxed text-slate-500">{g.description}</p>
                      {g.indicators?.length > 0 && (
                        <ul className="mt-3 space-y-1">
                          {g.indicators.map((ind) => (
                            <li key={ind.indicator_code} className="text-xs text-slate-400">
                              <span className="font-medium text-slate-500">{ind.sdg_target}</span>{" "}
                              {ind.indicator_name}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
