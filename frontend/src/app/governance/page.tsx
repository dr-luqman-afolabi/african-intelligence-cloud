import type { Metadata } from "next";
import Link from "next/link";
import { GOVERNANCE } from "@/lib/governance";

export const metadata: Metadata = {
  title: "Trust & Governance — Data, Security, Responsible AI & Methodology",
  description:
    "How African Intelligence Cloud handles data governance, security, responsible AI, statistical methodology and accessibility — including how uploaded household microdata is protected.",
  alternates: { canonical: "/governance" },
};

export default function GovernancePage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <p className="section-label">Trust &amp; governance</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">
        How we handle data, and what we commit to
      </h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        Institutions that hold household microdata ask these questions before they share anything.
        These pages answer them in writing — specifically, and including where the platform falls
        short rather than only where it does well.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {GOVERNANCE.map((d) => (
          <Link key={d.slug} href={`/governance/${d.slug}`} className="card card-hover group p-6">
            <h2 className="text-lg font-bold text-aic-dark">{d.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">{d.summary}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aic-green">
              Read
              <span className="transition group-hover:translate-x-0.5">→</span>
            </span>
          </Link>
        ))}
        <Link href="/privacy" className="card card-hover group p-6">
          <h2 className="text-lg font-bold text-aic-dark">Privacy Policy</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            What personal data we collect, why, how long we keep it and your rights over it.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aic-green">
            Read
            <span className="transition group-hover:translate-x-0.5">→</span>
          </span>
        </Link>
        <Link href="/terms" className="card card-hover group p-6">
          <h2 className="text-lg font-bold text-aic-dark">Terms of Service</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            The terms governing use of the platform, including acceptable use and data ownership.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aic-green">
            Read
            <span className="transition group-hover:translate-x-0.5">→</span>
          </span>
        </Link>
      </div>

      <section className="mt-12 card p-8">
        <h2 className="text-2xl font-bold text-aic-dark">Organisational accountability</h2>
        <p className="mt-3 leading-relaxed text-slate-600">
          African Intelligence Cloud is an initiative of{" "}
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
          Questions about any of this, or a specific governance requirement for a data partnership,
          go to{" "}
          <a href="mailto:info.aic@hyrin.org" className="font-medium text-aic-green underline underline-offset-4">
            info.aic@hyrin.org
          </a>
          .
        </p>
      </section>
    </div>
  );
}
