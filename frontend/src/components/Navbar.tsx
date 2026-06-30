import Link from "next/link";

export default function Navbar() {
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

      <div className="flex items-center gap-6 text-sm">
        <Link href="/dashboard" className="text-slate-300 hover:text-white transition">
          Dashboard
        </Link>
        <Link href="/datasets" className="text-slate-300 hover:text-white transition">
          Datasets
        </Link>
        <Link href="/connectors" className="text-slate-300 hover:text-white transition">
          Connectors
        </Link>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-300 hover:text-white transition"
        >
          API Docs
        </a>
        <span className="px-3 py-1 bg-aic-green text-white text-xs rounded-full font-semibold">
          Sprint 3
        </span>
      </div>
    </nav>
  );
}
