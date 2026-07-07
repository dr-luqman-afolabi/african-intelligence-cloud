"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import Logo from "@/components/ui/Logo";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/microdata", label: "Microdata Studio" },
  { href: "/research", label: "AI Research" },
  { href: "/datasets", label: "Datasets" },
  { href: "/connectors", label: "Connectors" },
  { href: "/sdg", label: "SDG" },
  { href: "/search", label: "Search" },
  { href: "/about", label: "About" },
];

const API_DOCS_URL = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`;

export default function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <nav
      className={clsx(
        "sticky top-0 z-50 transition-all",
        scrolled
          ? "bg-aic-dark/95 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-aic-dark/80"
          : "bg-aic-dark"
      )}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
        <Link href="/" className="text-white shrink-0">
          <Logo />
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {NAV_LINKS.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "rounded-lg px-3 py-2 text-sm font-medium transition",
                  active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"
                )}
              >
                {label}
              </Link>
            );
          })}
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
            {NAV_LINKS.map(({ href, label }) => {
              const active = pathname?.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={clsx(
                    "rounded-lg px-3 py-2.5 text-sm font-medium transition",
                    active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"
                  )}
                >
                  {label}
                </Link>
              );
            })}
            <a
              href={API_DOCS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/5 hover:text-white"
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
