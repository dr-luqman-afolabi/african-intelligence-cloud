import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/ui/Logo";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Contact the African Intelligence Cloud (AIC) team — for research partnerships, institutional access, data licensing, technical support, and general enquiries.",
  alternates: { canonical: "/contact" },
};

const CHANNELS = [
  {
    label: "General & partnerships",
    value: "aluqman@hyrin.org",
    href: "mailto:aluqman@hyrin.org",
    note: "Research collaboration, institutional access, data licensing, and media enquiries.",
  },
  {
    label: "Technical support",
    value: "aluqman@hyrin.org",
    href: "mailto:aluqman@hyrin.org?subject=AIC%20Support",
    note: "Account issues, dataset uploads, and questions about analysis or the platform.",
  },
];

export default function ContactPage() {
  return (
    <div>
      <section className="relative overflow-hidden bg-aic-hero px-4 pb-14 pt-20 sm:pt-24">
        <div className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-aic-green/10 blur-3xl" />
        <div className="relative mx-auto max-w-3xl text-center">
          <div className="mb-6 flex justify-center">
            <Logo size="lg" />
          </div>
          <p className="section-label">Contact</p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark sm:text-5xl">
            Get in touch
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-aic-muted">
            We work with universities, national statistical offices, governments, and development
            partners across Africa. Reach out and we typically respond within two business days.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl space-y-10 px-4 py-16">
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {CHANNELS.map((c) => (
            <div key={c.label} className="card p-6">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{c.label}</p>
              <a href={c.href} className="mt-2 block text-lg font-semibold text-aic-green hover:underline">
                {c.value}
              </a>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">{c.note}</p>
            </div>
          ))}
        </section>

        <section className="card p-8">
          <h2 className="text-2xl font-bold text-aic-dark">Organization</h2>
          <dl className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 text-sm">
            <div>
              <dt className="font-semibold text-slate-400">Platform</dt>
              <dd className="mt-1 text-slate-700">African Intelligence Cloud (AIC)</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-400">Focus</dt>
              <dd className="mt-1 text-slate-700">
                AI-powered research &amp; policy intelligence across all 54 African countries
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-400">Founder &amp; Director</dt>
              <dd className="mt-1 text-slate-700">Dr. Luqman Afolabi</dd>
            </div>
            <div>
              <dt className="font-semibold text-slate-400">Website</dt>
              <dd className="mt-1">
                <a href="https://aic.hyrin.org" className="text-aic-green hover:underline">
                  aic.hyrin.org
                </a>
              </dd>
            </div>
          </dl>
          <p className="mt-6 text-sm leading-relaxed text-slate-500">
            For institutional agreements, data-sharing arrangements, or restricted microdata access,
            please email us with your organization, intended use, and datasets of interest.
          </p>
        </section>

        <section className="rounded-2xl bg-aic-gradient p-8 text-center text-white shadow-glow">
          <h2 className="text-2xl font-bold">Prefer to explore first?</h2>
          <p className="mx-auto mt-2 max-w-xl text-white/80">
            The Macro Dashboard, Microdata Studio, and SDG Tracker are open to browse — no account
            required.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link href="/dashboard" className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark transition hover:bg-slate-100">
              Open Dashboard
            </Link>
            <Link href="/about" className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
              About AIC
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
