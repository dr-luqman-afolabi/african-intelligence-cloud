"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/datasets", label: "Datasets" },
  { href: "/surveys", label: "Microdata" },
  { href: "/connectors", label: "Connectors" },
  { href: "/health", label: "Health" },
  { href: "/search", label: "Search" },
  { href: "/sdg", label: "SDG" },
  { href: "/research", label: "AI Research" },
  { href: "/about", label: "About" },
    { href: "/microdata", label: "Microdata Studio" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-aic-dark text-white px-6 py-4 flex items-center justify-between shadow">
      <Link href="/" className="flex items-center gap-3 font-bold text-lg tracking-tight">
        <span className="flex gap-0.5">
          <span className="w-1.5 h-6 rounded bg-aic-green" />
          <span className="w-1.5 h-6 rounded bg-aic-gold" />
          <span className="w-1.5 h-6 rounded bg-aic-red" />
        </span>
        AIC
      </Link>

      <div className="flex items-center gap-5 text-sm">
        {NAV_LINKS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "transition",
              pathname?.startsWith(href)
                ? "text-white font-semibold"
                : "text-slate-300 hover:text-white"
            )}
          >
            {label}
          </Link>
        ))}
        <a
          href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-300 hover:text-white transition"
        >
          API Docs
        </a>
        <Link
            href="/profile"
            className="text-slate-300 hover:text-white transition"
          >
            Profile
          </Link>
          <Link
          href="/login"
          className="text-slate-300 hover:text-white transition"
        >
          Login
        </Link>
        <span className="px-3 py-1 bg-aic-green text-white text-xs rounded-full font-semibold">
          Sprint 6
        </span>
      </div>
    </nav>
  );
}
