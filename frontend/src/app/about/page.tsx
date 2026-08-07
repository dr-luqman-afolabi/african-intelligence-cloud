import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/ui/Logo";
import { CHALLENGES } from "@/lib/about";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "African Intelligence Cloud (AIC) is an AI-powered African research and policy intelligence platform integrating data discovery, microdata analytics, spatial intelligence, and AI-assisted research for Africa.",
  alternates: { canonical: "/about" },
};

// Deeper material lives on its own pages rather than extending this one — it
// had grown into several essays at a single URL, which buried the parts a
// first-time reader actually needs.
const MORE = [
  {
    href: "/about/technology",
    title: "Technology & capabilities",
    body: "The four capabilities behind the platform, who it is built for, and the long-term ambition.",
  },
  {
    href: "/about/leadership",
    title: "Leadership & governance",
    body: "The team, their credentials, the governance structure, and a message from the founder.",
  },
  {
    href: "/governance",
    title: "Trust & governance",
    body: "Data governance, security, responsible AI, methodology and accessibility.",
  },
  {
    href: "/partners",
    title: "Partner with AIC",
    body: "Data partnerships, government deployments, research collaboration and funding.",
  },
];

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-aic-hero px-4 pb-16 pt-20 sm:pt-24">
        <div className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-aic-green/10 blur-3xl animate-float" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-64 w-64 rounded-full bg-aic-navy/10 blur-3xl" />

        <div className="relative mx-auto max-w-3xl text-center">
          <div className="mb-6 flex justify-center animate-fade-in">
            <Logo variant="full" size="lg" />
          </div>
          <p className="section-label animate-fade-in">About us</p>
          <h1 className="mt-2 animate-fade-in-up text-4xl font-bold tracking-tight text-aic-dark sm:text-5xl">
            African Intelligence Cloud
          </h1>
          <p
            className="mx-auto mt-4 max-w-2xl animate-fade-in-up text-lg italic text-aic-muted"
            style={{ animationDelay: "0.1s" }}
          >
            Reimagining African research through AI, data and policy intelligence
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl space-y-14 px-4 pb-20 pt-14">
        {/* The problem, condensed from three essay-length paragraphs. */}
        <section className="card space-y-4 p-8 leading-relaxed text-slate-700">
          <p>
            Africa has one of the fastest-growing development data ecosystems in the world.
            Governments, statistical offices, universities and development partners have invested
            heavily in household surveys, censuses, administrative records and macroeconomic
            statistics — EICV, UNPS, DHS, LSMS, MICS and thousands of national publications.
          </p>
          <p>
            Yet a research utilization gap persists. Data sits across many institutions in
            incompatible formats under different licences, and usually needs advanced statistical
            software and technical expertise to analyse. Researchers spend more time locating,
            cleaning and harmonizing data than generating evidence, while policymakers lack timely,
            reproducible analysis that turns it into decisions.
          </p>
          <p>
            Existing tools each solve part of this. Data portals disseminate but do not analyse.
            Statistical software analyses but does not reach the data. AI assistants generate text
            but rarely connect to trusted African datasets. AIC exists to close that gap in one
            place.
          </p>
        </section>

        {/* Why AIC exists */}
        <section>
          <p className="section-label">Why AIC exists</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">The gap AIC fills</h2>
          <p className="mt-3 leading-relaxed text-aic-muted">
            Rather than another repository or dashboard, AIC integrates data discovery, secure data
            management, statistical analysis, geospatial analytics, artificial intelligence and
            collaborative research into a single cloud platform.
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {CHALLENGES.map((c, i) => (
              <div
                key={c.title}
                className="card card-hover animate-fade-in-up p-5"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <h3 className="mb-1.5 font-semibold text-aic-green">{c.title}</h3>
                <p className="text-sm text-slate-500">{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Vision / Mission */}
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="rounded-2xl bg-aic-gradient p-8 text-white shadow-glow-navy">
            <p className="text-xs font-bold uppercase tracking-widest text-white/60">Vision</p>
            <p className="mt-3 leading-relaxed text-white/85">
              To become Africa&apos;s leading AI-powered research and policy intelligence platform,
              enabling governments, researchers and development partners to transform data into
              evidence, evidence into policy, and policy into sustainable development outcomes.
            </p>
          </div>
          <div className="rounded-2xl bg-aic-gradient p-8 text-white shadow-glow-navy">
            <p className="text-xs font-bold uppercase tracking-widest text-white/60">Mission</p>
            <p className="mt-3 leading-relaxed text-white/85">
              To democratize access to high-quality African data, advanced analytics, geospatial
              intelligence and artificial intelligence through a secure, collaborative cloud
              platform that strengthens research capacity and evidence-based decision-making across
              the continent.
            </p>
          </div>
        </section>

        {/* Deeper material */}
        <section>
          <p className="section-label">Go deeper</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">More about AIC</h2>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {MORE.map((m) => (
              <Link key={m.href} href={m.href} className="card card-hover group p-6">
                <h3 className="font-semibold text-aic-dark">{m.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{m.body}</p>
                <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-aic-green">
                  Read
                  <span className="transition group-hover:translate-x-0.5">→</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>

      {/* CTA band */}
      <section className="bg-aic-gradient px-6 py-16">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-5 text-center">
          <h2 className="text-3xl font-bold text-white">Ready to explore the data?</h2>
          <p className="max-w-xl text-white/80">
            Join the researchers and institutions using AIC to turn African data into evidence, and
            evidence into policy.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/register"
              className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark shadow-glow transition hover:bg-slate-100"
            >
              Create free account
            </Link>
            <Link
              href="/countries"
              className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Browse 54 countries
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
