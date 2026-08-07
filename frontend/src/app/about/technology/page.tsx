import type { Metadata } from "next";
import Link from "next/link";
import { PILLARS, AUDIENCE } from "@/lib/about";

export const metadata: Metadata = {
  title: "Technology & Capabilities",
  description:
    "The four capabilities behind African Intelligence Cloud: African data integration, cloud-based microdata analytics, spatial development intelligence, and AI-assisted research.",
  alternates: { canonical: "/about/technology" },
};

export default function TechnologyPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <nav className="text-sm text-slate-400">
        <Link href="/about" className="hover:text-aic-green">
          About
        </Link>{" "}
        / <span className="text-slate-600">Technology</span>
      </nav>

      <p className="section-label mt-4">Capabilities</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">
        What Makes AIC Different
      </h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        Existing data portals focus on dissemination. Statistical software emphasises analysis
        without integrated data access. AI assistants generate text but rarely connect to trusted
        African datasets. AIC combines four capabilities that are rarely available in one system.
      </p>

      <div className="mt-9 space-y-4">
        {PILLARS.map((p, i) => (
          <div
            key={p.number}
            className="card animate-fade-in-up flex gap-4 p-6"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-aic-green/10 font-bold text-aic-green">
              {p.number}
            </span>
            <div>
              <h2 className="mb-1.5 font-semibold text-aic-dark">{p.title}</h2>
              <p className="text-sm leading-relaxed text-slate-500">{p.body}</p>
            </div>
          </div>
        ))}
      </div>

      <section className="mt-12 card p-8">
        <p className="section-label">Community</p>
        <h2 className="mt-2 text-2xl font-bold text-aic-dark">Built for Africa&apos;s Research Community</h2>
        <div className="mt-5 flex flex-wrap gap-2">
          {AUDIENCE.map((a) => (
            <span key={a} className="badge bg-aic-green/10 text-aic-green">
              {a}
            </span>
          ))}
        </div>
        <p className="mt-5 text-sm leading-relaxed text-slate-500">
          The platform supports both teaching and professional research by reducing technical
          barriers while maintaining rigorous analytical standards.
        </p>
      </section>

      <section className="mt-8 card p-8">
        <p className="section-label">Looking ahead</p>
        <h2 className="mt-2 text-2xl font-bold text-aic-dark">Our Long-Term Ambition</h2>
        <p className="mt-3 leading-relaxed text-slate-600">
          African Intelligence Cloud is more than a technology platform. It is continental digital
          research infrastructure designed to support Africa&apos;s knowledge economy — reducing the
          time between data collection and policy action, fostering cross-country learning,
          strengthening institutional research capacity, and accelerating progress toward the
          African Union Agenda 2063 and the United Nations Sustainable Development Goals.
        </p>
      </section>

      <section className="mt-8 card p-6">
        <h2 className="font-semibold text-aic-dark">How the analysis actually works</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          For the estimators behind these capabilities — FGT poverty indices, Gini, survey
          weighting, Moran&apos;s I and LISA clustering — and the assumptions they carry, see the{" "}
          <Link href="/governance/methodology" className="font-medium text-aic-green underline underline-offset-4">
            methodology page
          </Link>
          .
        </p>
      </section>

      <nav className="mt-12 border-t border-slate-100 pt-6">
        <p className="text-sm font-semibold text-slate-500">More about AIC</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/about" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            About
          </Link>
          <Link href="/about/leadership" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Leadership
          </Link>
          <Link href="/solutions" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Solutions
          </Link>
          <Link href="/governance" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Trust &amp; governance
          </Link>
        </div>
      </nav>
    </div>
  );
}
