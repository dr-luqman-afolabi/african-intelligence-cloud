import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Partner with AIC — Data, Research & Institutional Partnerships",
  description:
    "Partnership pathways with African Intelligence Cloud: data partnerships with statistical offices, research collaboration with universities, government deployments, and funding to scale Africa's data and policy intelligence infrastructure.",
  alternates: { canonical: "/partners" },
};

const PARTNERSHIPS = [
  {
    title: "Data partnerships",
    who: "National statistical offices, ministries, data producers",
    body: "Make a survey series or administrative dataset analysable within AIC while retaining control of it. Access conditions, licensing and attribution are configured per dataset — restricted microdata stays restricted.",
  },
  {
    title: "Government deployments",
    who: "Ministries, planning commissions, central banks",
    body: "Country-specific deployment for national monitoring, poverty targeting and development plan reporting, with analyst training so the capability stays in-house.",
  },
  {
    title: "Research partnerships",
    who: "Universities, research institutes, think tanks",
    body: "Institutional access for teaching and research, joint methodological work, and reproducible analysis environments for supervised student projects.",
  },
  {
    title: "Development partners",
    who: "Multilaterals, bilateral agencies, foundations",
    body: "Programme design and monitoring evidence across portfolios, with the provenance of every figure visible and analyses that country teams can rerun themselves.",
  },
  {
    title: "Technology partnerships",
    who: "Cloud, data and analytics providers",
    body: "Integration of additional data sources, analytical methods or infrastructure into the platform.",
  },
  {
    title: "Funding & investment",
    who: "Innovation funds, impact investors, grant-makers",
    body: "We are seeking strategic partners to scale Africa's data and policy intelligence infrastructure — extending country coverage, deepening microdata integration and widening institutional access.",
  },
];

export default function PartnersPage() {
  return (
    <div>
      <section className="bg-aic-hero px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <p className="section-label">Partnerships</p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark sm:text-5xl">
            Partner with AIC
          </h1>
          <p className="mt-4 max-w-3xl text-lg leading-relaxed text-aic-muted">
            African Intelligence Cloud is building continental infrastructure for turning African
            data into evidence. That is not something any single organisation builds alone — it
            depends on the institutions that produce the data, the researchers who interrogate it,
            and the governments and partners who act on it.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl px-6 py-14">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          {PARTNERSHIPS.map((p) => (
            <div key={p.title} className="card p-6">
              <h2 className="font-bold text-aic-dark">{p.title}</h2>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                {p.who}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-slate-500">{p.body}</p>
            </div>
          ))}
        </div>

        <section className="mt-14">
          <h2 className="text-2xl font-bold text-aic-dark">What a partnership involves</h2>
          <ol className="mt-5 space-y-4">
            {[
              "Tell us what you are trying to achieve and the constraints you are working under — data sensitivity, timelines, existing systems.",
              "We assess what is feasible with what exists today, and are explicit about what would need building.",
              "We agree scope, data governance terms and attribution in writing before any data moves.",
              "Delivery, with training where the capability needs to remain with your team.",
            ].map((step, i) => (
              <li key={step} className="flex gap-4">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-aic-green/10 text-sm font-bold text-aic-green">
                  {i + 1}
                </span>
                <span className="pt-0.5 leading-relaxed text-slate-600">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-14 card p-8">
          <h2 className="text-2xl font-bold text-aic-dark">Governance & accountability</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            AIC is an initiative of{" "}
            <a
              href="https://hyrin.org"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-aic-green underline underline-offset-4"
            >
              H.Y.R.I.N. — Holistic Youth Resilience &amp; Innovation Network
            </a>
            , a non-profit registered with the Corporate Affairs Commission of Nigeria
            (CAC&nbsp;RC&nbsp;8729824), governed by an independent board and subject to annual
            external audit.
          </p>
          <p className="mt-3 leading-relaxed text-slate-600">
            Uploaded microdata is held in access-controlled storage and is never redistributed.
            Public data carries the licence of its original provider, shown per source in the{" "}
            <Link href="/connectors" className="font-medium text-aic-green underline underline-offset-4">
              data source catalogue
            </Link>
            .
          </p>
          <div className="mt-5 flex flex-wrap gap-3 text-sm">
            <Link href="/about" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
              Leadership team
            </Link>
            <Link href="/privacy" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
              Privacy policy
            </Link>
            <Link href="/terms" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
              Terms of service
            </Link>
          </div>
        </section>

        <section className="mt-14 rounded-2xl bg-aic-gradient p-8 text-center text-white shadow-glow">
          <h2 className="text-2xl font-bold">Start a conversation</h2>
          <p className="mx-auto mt-2 max-w-xl text-white/80">
            Tell us your organisation, what you are working on, and what you would need from a
            partnership. We typically respond within two business days.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <a
              href="mailto:aluqman@hyrin.org?subject=AIC%20Partnership%20enquiry"
              className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark transition hover:bg-slate-100"
            >
              Email the director
            </a>
            <Link
              href="/contact"
              className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Contact page
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
