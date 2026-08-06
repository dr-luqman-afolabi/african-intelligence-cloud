import type { Metadata } from "next";
import Link from "next/link";
import { SOLUTIONS } from "@/lib/solutions";

export const metadata: Metadata = {
  title: "Solutions — AIC for Governments, Researchers & Development Partners",
  description:
    "How African Intelligence Cloud is used by governments, development partners, universities, researchers, NGOs and business: poverty targeting, SDG monitoring, econometric research and market analysis.",
  alternates: { canonical: "/solutions" },
};

export default function SolutionsPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <p className="section-label">Solutions</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">
        Built for the people who use African data
      </h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        The same platform serves very different questions — a ministry targeting a transfer
        programme, a supervisor marking a dissertation, an investor comparing markets. These pages
        set out what AIC does for each, and which products do it.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-5 md:grid-cols-2">
        {SOLUTIONS.map((s) => (
          <Link key={s.slug} href={`/solutions/${s.slug}`} className="card card-hover group p-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              {s.audience}
            </p>
            <h2 className="mt-1 text-xl font-bold text-aic-dark">{s.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">{s.summary}</p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {s.capabilities.map((c) => (
                <span key={c.product} className="badge bg-aic-green/10 text-aic-green">
                  {c.product}
                </span>
              ))}
            </div>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aic-green">
              Read more
              <span className="transition group-hover:translate-x-0.5">→</span>
            </span>
          </Link>
        ))}
      </div>

      <section className="mt-14 rounded-2xl bg-aic-gradient p-8 text-center text-white shadow-glow">
        <h2 className="text-2xl font-bold">Working on something specific?</h2>
        <p className="mx-auto mt-2 max-w-xl text-white/80">
          We work with institutions on data partnerships, capacity building and deployments tailored
          to a national context.
        </p>
        <Link
          href="/partners"
          className="mt-5 inline-block rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark transition hover:bg-slate-100"
        >
          Partner with AIC
        </Link>
      </section>
    </div>
  );
}
