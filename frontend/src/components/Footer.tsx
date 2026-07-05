import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-aic-dark text-slate-300 mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 sm:grid-cols-3 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="w-1.5 h-6 rounded bg-aic-green" />
            <span className="w-1.5 h-6 rounded bg-aic-gold" />
            <span className="w-1.5 h-6 rounded bg-aic-red" />
            <span className="font-bold text-white">African Intelligence Cloud</span>
          </div>
          <p className="text-sm text-slate-400">
            Macroeconomic data, analytics, and policy intelligence for Africa.
          </p>
        </div>
        <div>
          <h4 className="text-white font-semibold text-sm mb-3">Quick Links</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/dashboard" className="hover:text-white transition">Dashboard</Link></li>
            <li><Link href="/sdg" className="hover:text-white transition">SDG Analytics</Link></li>
            <li><Link href="/surveys" className="hover:text-white transition">Microdata</Link></li>
            <li><Link href="/research" className="hover:text-white transition">AI Research</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold text-sm mb-3">Contact</h4>
          <p className="text-sm">
            <a href="mailto:aluqman@hyrin.org" className="hover:text-white transition">
              aluqman@hyrin.org
            </a>
          </p>
          <p className="text-sm text-slate-400 mt-2">
            Dr. Luqman Afolabi &mdash; Founder &amp; Director
          </p>
        </div>
      </div>
      <div className="border-t border-slate-700 py-4 text-center text-xs text-slate-500">
        &copy; {new Date().getFullYear()} African Intelligence Cloud. All rights reserved.
      </div>
    </footer>
  );
}
