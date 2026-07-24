import Link from "next/link";
import Logo from "@/components/ui/Logo";

const COLUMNS = [
  {
    title: "Platform",
    links: [
      { href: "/dashboard", label: "Dashboard" },
      { href: "/microdata", label: "Microdata & Poverty" },
      { href: "/research", label: "AI Research" },
      { href: "/sdg", label: "SDG Tracker" },
    ],
  },
  {
    title: "Data",
    links: [
      { href: "/datasets", label: "Datasets" },
      { href: "/surveys", label: "Surveys" },
      { href: "/connectors", label: "Connectors" },
      { href: "/search", label: "Search" },
      { href: "/health", label: "Source Health" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/about", label: "About" },
      { href: "/contact", label: "Contact" },
      { href: "/login", label: "Sign in" },
      { href: "/register", label: "Create account" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/privacy", label: "Privacy Policy" },
      { href: "/terms", label: "Terms of Service" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-5">
          <div className="col-span-2 sm:col-span-1">
            <Logo />
            <p className="mt-3 max-w-xs text-sm text-aic-muted">
              Macroeconomic data, microdata poverty analysis, and Africa-wide GIS mapping — policy
              intelligence for every African country.
            </p>
            <p className="mt-3 max-w-xs text-sm text-aic-muted">
              An initiative of{" "}
              <a
                href="https://hyrin.org"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-aic-green underline underline-offset-4"
              >
                H.Y.R.I.N. — Holistic Youth Resilience &amp; Innovation Network
              </a>
              .
            </p>
            <p className="mt-4 text-sm text-aic-muted">
              <a href="mailto:aluqman@hyrin.org" className="transition hover:text-aic-green">
                aluqman@hyrin.org
              </a>
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{col.title}</p>
              <ul className="mt-3 space-y-2">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-slate-600 transition hover:text-aic-green">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-slate-100 pt-6 text-xs text-slate-400 sm:flex-row">
          <p>© {new Date().getFullYear()} African Intelligence Cloud. Built for policy intelligence across Africa.</p>
          <div className="flex gap-1">
            <span className="h-1.5 w-6 rounded-full bg-aic-green" />
            <span className="h-1.5 w-6 rounded-full bg-aic-gold" />
            <span className="h-1.5 w-6 rounded-full bg-aic-red" />
          </div>
        </div>
      </div>
    </footer>
  );
}
