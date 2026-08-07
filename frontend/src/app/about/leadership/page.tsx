import type { Metadata } from "next";
import Link from "next/link";
import { TEAM, HYRIN_URL } from "@/lib/about";

export const metadata: Metadata = {
  title: "Leadership & Governance",
  description:
    "The leadership team behind African Intelligence Cloud — economists, public health and financial governance specialists — and the governance structure they operate under.",
  alternates: { canonical: "/about/leadership" },
};

export default function LeadershipPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <nav className="text-sm text-slate-400">
        <Link href="/about" className="hover:text-aic-green">
          About
        </Link>{" "}
        / <span className="text-slate-600">Leadership</span>
      </nav>

      <p className="section-label mt-4">Our people</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">Leadership &amp; Governance</h1>
      <p className="mt-3 max-w-3xl leading-relaxed text-aic-muted">
        AIC is delivered by a team combining rigorous academic training, international development
        expertise, and lived experience of the communities we serve. The platform is an initiative
        of{" "}
        <a
          href={HYRIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-aic-green underline underline-offset-4"
        >
          HYRIN — Holistic Youth Resilience &amp; Innovation Network
        </a>
        , a registered Nigerian non-profit (CAC&nbsp;RC&nbsp;8729824). Each profile below is
        publicly verifiable on the HYRIN website.
      </p>

      <div className="mt-9 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {TEAM.map((m, i) => (
          <div
            key={m.name}
            className="card animate-fade-in-up flex gap-4 p-6"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-aic-navy text-lg font-bold text-white">
              {m.initials}
            </span>
            <div className="min-w-0">
              <p className="font-semibold text-aic-dark">{m.name}</p>
              <p className="text-sm font-medium text-aic-green">{m.role}</p>
              <p className="mt-0.5 text-xs uppercase tracking-wide text-slate-400">{m.credentials}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">{m.bio}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                <a
                  href={`${HYRIN_URL}/about.html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-aic-green hover:underline"
                >
                  Verify profile on HYRIN ↗
                </a>
                {m.email && (
                  <a href={`mailto:${m.email}`} className="text-slate-500 hover:text-aic-green">
                    {m.email}
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap gap-3 text-sm">
        <a
          href={HYRIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="badge bg-aic-green/10 text-aic-green"
        >
          Parent organization: hyrin.org ↗
        </a>
        <a
          href="https://www.linkedin.com/company/hyrin-ng"
          target="_blank"
          rel="noopener noreferrer"
          className="badge bg-aic-green/10 text-aic-green"
        >
          HYRIN on LinkedIn ↗
        </a>
        <span className="badge bg-slate-100 text-slate-500">CAC Registered NGO · RC 8729824</span>
        <span className="badge bg-slate-100 text-slate-500">Annual independent external audits</span>
      </div>

      {/* Director's message — kept here rather than on the landing page, which
          should introduce the platform before introducing a person. */}
      <section className="mt-14 card p-8">
        <p className="section-label">From the founder</p>
        <h2 className="mt-2 text-3xl font-bold text-aic-dark">Message from the Director</h2>
        <div className="mt-6 space-y-4 leading-relaxed text-slate-600">
          <p>Welcome to the African Intelligence Cloud.</p>
          <p>
            Africa stands at a pivotal moment in its development journey. Governments, universities,
            national statistical offices and research institutions are producing unprecedented
            volumes of high-quality data. Yet much of it remains fragmented, underutilized, and
            difficult to translate into timely policy decisions.
          </p>
          <p>The African Intelligence Cloud was established to bridge that gap.</p>
          <p>
            AIC is built on the belief that evidence should drive development. By combining trusted
            African datasets, advanced analytics, geospatial intelligence, artificial intelligence
            and collaborative research tools, we aim to reduce the distance between data collection
            and policy action.
          </p>
          <p>
            We invite researchers, institutions, governments, development organizations and
            technology partners to join us in building a future where African data generates African
            solutions for African challenges.
          </p>
          <p className="font-medium text-aic-dark">
            Together, we can transform data into knowledge, knowledge into policy, and policy into
            sustainable development.
          </p>
        </div>

        <div className="mt-8 flex items-center gap-4 border-t border-slate-100 pt-6">
          <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-aic-green text-xl font-bold text-white">
            LA
          </span>
          <div>
            <p className="font-semibold text-aic-dark">Dr. Luqman Afolabi</p>
            <p className="text-sm text-slate-500">Founder &amp; Director, African Intelligence Cloud</p>
            <a href="mailto:aluqman@hyrin.org" className="text-sm text-aic-green hover:underline">
              aluqman@hyrin.org
            </a>
          </div>
        </div>
      </section>

      <nav className="mt-12 border-t border-slate-100 pt-6">
        <p className="text-sm font-semibold text-slate-500">More about AIC</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/about" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            About
          </Link>
          <Link href="/about/technology" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Technology
          </Link>
          <Link href="/governance" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Trust &amp; governance
          </Link>
          <Link href="/partners" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Partner with AIC
          </Link>
        </div>
      </nav>
    </div>
  );
}
