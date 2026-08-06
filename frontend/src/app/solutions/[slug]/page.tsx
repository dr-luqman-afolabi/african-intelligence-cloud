import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SOLUTIONS, getSolution } from "@/lib/solutions";

export function generateStaticParams() {
  return SOLUTIONS.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const s = getSolution(slug);
  if (!s) return { title: "Solution not found" };
  return {
    title: s.title,
    description: s.summary,
    alternates: { canonical: `/solutions/${s.slug}` },
    openGraph: { title: s.title, description: s.summary, url: `/solutions/${s.slug}` },
  };
}

function isExternal(href: string) {
  return href.startsWith("http");
}

export default async function SolutionPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const s = getSolution(slug);
  if (!s) notFound();

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <nav className="text-sm text-slate-400">
        <Link href="/solutions" className="hover:text-aic-green">
          Solutions
        </Link>{" "}
        / <span className="text-slate-600">{s.audience}</span>
      </nav>

      <p className="section-label mt-4">{s.audience}</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight text-aic-dark">{s.title}</h1>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed text-aic-muted">{s.summary}</p>

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-aic-dark">What this audience needs</h2>
        <ul className="mt-4 space-y-2">
          {s.needs.map((n) => (
            <li key={n} className="flex gap-3 text-slate-600">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-aic-green" />
              <span className="leading-relaxed">{n}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-bold text-aic-dark">How AIC answers it</h2>
        <div className="mt-5 space-y-3">
          {s.capabilities.map((c) =>
            isExternal(c.href) ? (
              <a
                key={c.name}
                href={c.href}
                target="_blank"
                rel="noopener noreferrer"
                className="card card-hover block p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <h3 className="font-semibold text-aic-dark">{c.name}</h3>
                  <span className="badge shrink-0 bg-aic-green/10 text-aic-green">{c.product} ↗</span>
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{c.description}</p>
              </a>
            ) : (
              <Link key={c.name} href={c.href} className="card card-hover block p-5">
                <div className="flex items-start justify-between gap-4">
                  <h3 className="font-semibold text-aic-dark">{c.name}</h3>
                  <span className="badge shrink-0 bg-aic-green/10 text-aic-green">{c.product}</span>
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{c.description}</p>
              </Link>
            ),
          )}
        </div>
      </section>

      <section className="mt-12 card p-8">
        <p className="section-label">In practice</p>
        <h2 className="mt-2 text-2xl font-bold text-aic-dark">{s.example.title}</h2>
        <ol className="mt-5 space-y-3">
          {s.example.steps.map((step, i) => (
            <li key={step} className="flex gap-4">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-aic-green/10 text-sm font-bold text-aic-green">
                {i + 1}
              </span>
              <span className="pt-0.5 leading-relaxed text-slate-600">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-12 rounded-2xl bg-aic-gradient p-8 text-center text-white shadow-glow">
        <h2 className="text-2xl font-bold">Discuss a deployment</h2>
        <p className="mx-auto mt-2 max-w-xl text-white/80">
          We work with institutions on data partnerships, capacity building and country-specific
          deployments.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Link
            href="/partners"
            className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark transition hover:bg-slate-100"
          >
            Partner with AIC
          </Link>
          <Link
            href="/contact"
            className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
          >
            Contact us
          </Link>
        </div>
      </section>

      <nav className="mt-12 border-t border-slate-100 pt-6">
        <p className="text-sm font-semibold text-slate-500">Other audiences</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {SOLUTIONS.filter((o) => o.slug !== s.slug).map((o) => (
            <Link key={o.slug} href={`/solutions/${o.slug}`} className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
              {o.title.replace("AIC for ", "")}
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}
