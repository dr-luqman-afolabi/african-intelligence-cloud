import Link from "next/link";
import Logo from "@/components/ui/Logo";

const STATS = [
  { value: "54", label: "African countries supported" },
  { value: "30+", label: "Macro indicators tracked" },
  { value: "FGT0–2", label: "Poverty indices computed" },
  { value: "Moran's I", label: "Spatial clustering analysis" },
];

const FEATURES = [
  {
    title: "Macro Dashboard",
    description: "Historical GDP, inflation, poverty, trade, and debt indicators sourced from the World Bank, visualized over 30 years.",
    href: "/dashboard",
    icon: <path d="M3 3v18h18M7 15l4-4 3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />,
  },
  {
    title: "Microdata & Poverty Studio",
    description: "Upload household survey microdata and compute FGT poverty indices, Gini coefficients, and welfare distributions — for any African country.",
    href: "/microdata",
    icon: <path d="M12 3v18M3 12h18M5 5l14 14M19 5L5 19" strokeLinecap="round" />,
  },
  {
    title: "Africa-wide GIS Mapping",
    description: "Upload GADM, HDX, or Natural Earth boundaries and render choropleth poverty maps with Moran's I and LISA cluster analysis.",
    href: "/microdata/spatial",
    icon: <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z M12 12a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" strokeLinecap="round" strokeLinejoin="round" />,
  },
  {
    title: "AI Research Assistant",
    description: "Search papers, generate literature reviews, recommend theories/methods, and get AI-powered variable recommendations.",
    href: "/research",
    icon: <path d="M9.5 3a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM21 21l-4.35-4.35" strokeLinecap="round" />,
  },
  {
    title: "SDG Tracker",
    description: "Track progress against all 17 Sustainable Development Goals with indicator-level data for every tracked country.",
    href: "/sdg",
    icon: <path d="M4 21V9M12 21V3M20 21v-7" strokeLinecap="round" />,
  },
  {
    title: "40+ Data Connectors",
    description: "Live health monitoring across World Bank, DHS, HDX, IPUMS, and dozens more African-focused data sources.",
    href: "/connectors",
    icon: <path d="M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 010 20 15 15 0 010-20z" strokeLinecap="round" />,
  },
];

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-aic-hero px-4 pb-20 pt-20 sm:pt-28">
        <div className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-aic-green/10 blur-3xl animate-float" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-64 w-64 rounded-full bg-aic-gold/10 blur-3xl" />

        <div className="relative mx-auto max-w-4xl text-center">
          <div className="mb-6 flex justify-center animate-fade-in">
            <Logo size="lg" />
          </div>

          <h1 className="animate-fade-in-up text-4xl font-bold tracking-tight text-aic-dark sm:text-6xl">
            Policy intelligence, <span className="text-aic-green">built for Africa</span>
          </h1>
          <p
            className="mx-auto mt-5 max-w-2xl animate-fade-in-up text-lg text-aic-muted sm:text-xl"
            style={{ animationDelay: "0.1s" }}
          >
            Macroeconomic data, household microdata poverty analysis, and Africa-wide GIS mapping —
            in one platform, for every African country.
          </p>

          <div
            className="mt-9 flex animate-fade-in-up flex-wrap justify-center gap-3"
            style={{ animationDelay: "0.2s" }}
          >
            <Link href="/dashboard" className="btn-primary px-6 py-3 text-base">
              Open Dashboard
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <Link href="/microdata" className="btn-secondary px-6 py-3 text-base">
              Explore Microdata Studio
            </Link>
          </div>
        </div>

        <div
          className="relative mx-auto mt-16 grid max-w-4xl animate-fade-in-up grid-cols-2 gap-4 sm:grid-cols-4"
          style={{ animationDelay: "0.3s" }}
        >
          {STATS.map((s) => (
            <div key={s.label} className="card px-4 py-5 text-center">
              <p className="text-2xl font-bold text-aic-dark">{s.value}</p>
              <p className="mt-1 text-xs text-slate-500">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Feature grid */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="section-label">Everything in one place</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">A comprehensive intelligence toolkit</h2>
          <p className="mt-3 text-aic-muted">
            From macro trends to household-level poverty mapping, AIC brings every layer of African
            development data into a single, interactive platform.
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Link
              key={f.title}
              href={f.href}
              className="card card-hover group flex flex-col gap-4 p-6 animate-fade-in-up"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-aic-green/10 text-aic-green transition group-hover:bg-aic-green group-hover:text-white">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  {f.icon}
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-aic-dark">{f.title}</h3>
                <p className="mt-1.5 text-sm text-slate-500">{f.description}</p>
              </div>
              <span className="mt-auto flex items-center gap-1 text-sm font-medium text-aic-green opacity-0 transition group-hover:opacity-100">
                Explore
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA band */}
      <section className="bg-aic-gradient px-6 py-16">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-5 text-center">
          <h2 className="text-3xl font-bold text-white">Ready to explore the data?</h2>
          <p className="max-w-xl text-white/80">
            Upload your household survey and see poverty, inequality, and spatial clustering results
            in minutes — no GIS expertise required.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/register" className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark shadow-glow transition hover:bg-slate-100">
              Create free account
            </Link>
            <Link href="/microdata" className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
              View Microdata Studio
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
