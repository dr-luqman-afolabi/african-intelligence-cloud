"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import Logo from "@/components/ui/Logo";
import { fetchCurrentUser } from "@/lib/api";

type NavLink = { href: string; label: string; hint?: string; external?: boolean };
type NavGroup = { label: string; items: NavLink[] };
type NavEntry = NavLink | NavGroup;

// Hosted JupyterHub (Python/R notebooks) — a separate service, so this is an
// absolute URL rather than an app route.
const ANALYTICS_STUDIO_URL = "https://studio.hyrin.org";

// Grouped as products rather than as a list of tools. A first-time visitor —
// or a funder — should meet the platform before meeting ten analytical modules,
// so the modules sit under Platform with their AIC product names and a line
// saying what each is for.
const NAV: NavEntry[] = [
  {
    label: "Platform",
    items: [
      { href: "/dashboard", label: "AIC Macro", hint: "Macroeconomic intelligence" },
      { href: "/microdata", label: "AIC Micro", hint: "Poverty & welfare analytics" },
      { href: "/microdata/explorer", label: "AIC Geo", hint: "Spatial development intelligence" },
      { href: "/microdata/intelligence", label: "AIC Intelligence", hint: "Ask questions in plain language" },
      { href: "/research", label: "AIC Research", hint: "AI-assisted research workflow" },
      { href: "/forecast", label: "AIC Forecast", hint: "Projections & scenarios" },
      { href: "/sdg", label: "AIC SDG", hint: "Sustainable Development Goals" },
      { href: ANALYTICS_STUDIO_URL, label: "Analytics Studio ↗", hint: "Python & R notebooks", external: true },
    ],
  },
  { href: "/countries", label: "Countries" },
  {
    label: "Data",
    items: [
      { href: "/surveys", label: "Survey Catalogue", hint: "LSMS, DHS, MICS & more" },
      { href: "/connectors", label: "Data Sources", hint: "46 catalogued connectors" },
      { href: "/microdata/indicators", label: "Agricultural Indicators" },
      { href: "/harveststat", label: "Crop Statistics" },
      { href: "/consumption", label: "Consumption Observatory" },
      { href: "/analysis-lab", label: "Automated Analysis Lab" },
      { href: "/datasets", label: "My Datasets", hint: "Your uploads" },
      { href: "/search", label: "Search" },
    ],
  },
  { href: "/about", label: "About" },
];

function isGroup(entry: NavEntry): entry is NavGroup {
  return (entry as NavGroup).items !== undefined;
}

/** Renders a nav item as a client-side Link, or a new-tab anchor when the
 *  destination is a separate service (e.g. the hosted JupyterHub). */
function NavItem({ item, className }: { item: NavLink; className: string }) {
  const body = item.hint ? (
    <>
      <span className="block">{item.label}</span>
      <span className="block text-xs text-slate-400">{item.hint}</span>
    </>
  ) : (
    item.label
  );

  if (item.external) {
    return (
      <a href={item.href} target="_blank" rel="noopener noreferrer" className={className}>
        {body}
      </a>
    );
  }
  return (
    <Link href={item.href} className={className}>
      {body}
    </Link>
  );
}

const ADMIN_ROLES = new Set(["super_admin", "org_admin"]);

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="opacity-70">
      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("aic_token");
    if (!token) return;
    fetchCurrentUser()
      .then((u) => {
        setIsAuthenticated(true);
        setIsAdmin(ADMIN_ROLES.has(u.role));
      })
      .catch(() => {
        setIsAuthenticated(false);
        setIsAdmin(false);
      });
  }, []);

  const linkActive = (href: string) => (href === "/" ? pathname === "/" : pathname?.startsWith(href));
  const groupActive = (g: NavGroup) => g.items.some((i) => pathname?.startsWith(i.href));

  const desktopLinkClass = (active: boolean) =>
    clsx(
      "rounded-lg px-3 py-2 text-sm font-medium transition",
      active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
    );

  return (
    <nav
      className={clsx(
        "sticky top-0 z-50 transition-all",
        scrolled
          ? "bg-aic-dark/95 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-aic-dark/80"
          : "bg-aic-dark",
      )}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
        <Link href="/" className="text-white shrink-0">
          <Logo variant="mark" size="sm" plate />
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {NAV.map((entry) =>
            isGroup(entry) ? (
              <div key={entry.label} className="relative group">
                <button type="button" className={clsx(desktopLinkClass(groupActive(entry)), "inline-flex items-center gap-1")}>
                  {entry.label}
                  <Chevron />
                </button>
                <div className="absolute left-0 top-full hidden pt-2 group-hover:block">
                  <div className="min-w-[268px] overflow-hidden rounded-xl border border-white/10 bg-aic-dark py-1 shadow-xl">
                    {entry.items.map((item) => (
                      <NavItem
                        key={item.href}
                        item={item}
                        className={clsx(
                          "block px-4 py-2.5 text-sm transition",
                          linkActive(item.href) ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
                        )}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <Link key={entry.href} href={entry.href} className={desktopLinkClass(!!linkActive(entry.href))}>
                {entry.label}
              </Link>
            ),
          )}
          {isAdmin && (
            <Link
              href="/admin/users"
              className={clsx(
                "rounded-lg px-3 py-2 text-sm font-medium transition",
                pathname?.startsWith("/admin")
                  ? "bg-amber-500/20 text-amber-300"
                  : "text-amber-400 hover:bg-amber-500/10 hover:text-amber-300",
              )}
            >
              Admin
            </Link>
          )}
        </div>

        <div className="hidden items-center gap-3 lg:flex">
          {isAuthenticated ? (
            <Link href="/profile" className="text-sm text-slate-300 transition hover:text-white">
              Profile
            </Link>
          ) : (
            <Link href="/login" className="btn-primary !py-2 !px-4 text-sm">
              Sign in
            </Link>
          )}
        </div>

        <button
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Toggle menu"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-white lg:hidden"
        >
          {mobileOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
            </svg>
          )}
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-white/10 bg-aic-dark px-4 pb-4 pt-2 lg:hidden animate-fade-in">
          <div className="flex flex-col gap-0.5">
            {NAV.map((entry) =>
              isGroup(entry) ? (
                <div key={entry.label} className="pt-2">
                  <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">{entry.label}</p>
                  {entry.items.map((item) => (
                    <NavItem
                      key={item.href}
                      item={item}
                      className={clsx(
                        "rounded-lg px-3 py-2.5 text-sm font-medium transition",
                        pathname?.startsWith(item.href) ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
                      )}
                    />
                  ))}
                </div>
              ) : (
                <Link
                  key={entry.href}
                  href={entry.href}
                  className={clsx(
                    "rounded-lg px-3 py-2.5 text-sm font-medium transition",
                    pathname?.startsWith(entry.href) ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
                  )}
                >
                  {entry.label}
                </Link>
              ),
            )}
            {isAdmin && (
              <Link
                href="/admin/users"
                className={clsx(
                  "mt-2 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                  pathname?.startsWith("/admin")
                    ? "bg-amber-500/20 text-amber-300"
                    : "text-amber-400 hover:bg-amber-500/10 hover:text-amber-300",
                )}
              >
                Admin
              </Link>
            )}
            {isAuthenticated ? (
              <Link
                href="/profile"
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
              >
                Profile
              </Link>
            ) : (
              <Link href="/login" className="btn-primary mt-2 !py-2.5 text-sm">
                Sign in
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
