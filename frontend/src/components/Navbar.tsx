"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import Logo from "@/components/ui/Logo";
import { fetchCurrentUser } from "@/lib/api";

type NavLink = { href: string; label: string };
type NavGroup = { label: string; items: NavLink[] };
type NavEntry = NavLink | NavGroup;

const NAV: NavEntry[] = [
  { href: "/dashboard", label: "Dashboard" },
  {
    label: "Analyze",
    items: [
      { href: "/microdata", label: "Microdata Studio" },
      { href: "/microdata/intelligence", label: "AIC Intelligence" },
      { href: "/microdata/indicators", label: "Ag Indicators" },
      { href: "/microdata/explorer", label: "Spatial Explorer" },
    ],
  },
  {
    label: "Data",
    items: [
      { href: "/datasets", label: "Datasets" },
      { href: "/surveys", label: "Survey Catalog" },
      { href: "/connectors", label: "Connectors" },
    ],
  },
  { href: "/research", label: "AI Research" },
  { href: "/sdg", label: "SDG" },
  { href: "/search", label: "Search" },
  { href: "/about", label: "About" },
];

function isGroup(entry: NavEntry): entry is NavGroup {
  return (entry as NavGroup).items !== undefined;
}

const ADMIN_ROLES = new Set(["super_admin", "org_admin"]);
const API_DOCS_URL = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`;

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
      .then((u) => setIsAdmin(ADMIN_ROLES.has(u.role)))
      .catch(() => {});
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
          <Logo />
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
                  <div className="min-w-[210px] overflow-hidden rounded-xl border border-white/10 bg-aic-dark py-1 shadow-xl">
                    {entry.items.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={clsx(
                          "block px-4 py-2.5 text-sm transition",
                          linkActive(item.href) ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
                        )}
                      >
                        {item.label}
                      </Link>
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
          <a
            href={API_DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-slate-300 transition hover:text-white"
          >
            API Docs
          </a>
          <Link href="/profile" className="text-sm text-slate-300 transition hover:text-white">
            Profile
          </Link>
          <Link href="/login" className="btn-primary !py-2 !px-4 text-sm">
            Sign in
          </Link>
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
                    <Link
                      key={item.href}
                      href={item.href}
                      className={clsx(
                        "rounded-lg px-3 py-2.5 text-sm font-medium transition",
                        pathname?.startsWith(item.href) ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
                      )}
                    >
                      {item.label}
                    </Link>
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
            <a
              href={API_DOCS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              API Docs
            </a>
            <Link
              href="/profile"
              className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Profile
            </Link>
            <Link href="/login" className="btn-primary mt-2 !py-2.5 text-sm">
              Sign in
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
