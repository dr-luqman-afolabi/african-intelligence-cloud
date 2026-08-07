import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { GOVERNANCE, getGovernanceDoc } from "@/lib/governance";

export function generateStaticParams() {
  return GOVERNANCE.map((d) => ({ slug: d.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = getGovernanceDoc(slug);
  if (!doc) return { title: "Not found" };
  return {
    title: doc.title,
    description: doc.summary,
    alternates: { canonical: `/governance/${doc.slug}` },
    openGraph: { title: doc.title, description: doc.summary, url: `/governance/${doc.slug}` },
  };
}

export default async function GovernanceDocPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = getGovernanceDoc(slug);
  if (!doc) notFound();

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <nav className="text-sm text-slate-400">
        <Link href="/governance" className="hover:text-aic-green">
          Trust &amp; governance
        </Link>{" "}
        / <span className="text-slate-600">{doc.title}</span>
      </nav>

      <h1 className="mt-4 text-4xl font-bold tracking-tight text-aic-dark">{doc.title}</h1>
      <p className="mt-3 text-lg leading-relaxed text-aic-muted">{doc.summary}</p>

      <div className="mt-10 space-y-10">
        {doc.sections.map((s) => (
          <section key={s.heading}>
            <h2 className="text-xl font-bold text-aic-dark">{s.heading}</h2>
            <div className="mt-3 space-y-3">
              {s.body.map((p) => (
                <p key={p} className="leading-relaxed text-slate-600">
                  {p}
                </p>
              ))}
            </div>
            {s.points && (
              <ul className="mt-4 space-y-2">
                {s.points.map((pt) => (
                  <li key={pt} className="flex gap-3 text-slate-600">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      className="mt-0.5 shrink-0 text-aic-green"
                    >
                      <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span className="leading-relaxed">{pt}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>

      <section className="mt-12 card p-6">
        <h2 className="font-semibold text-aic-dark">Questions about this?</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Email{" "}
          <a href="mailto:info.aic@hyrin.org" className="font-medium text-aic-green underline underline-offset-4">
            info.aic@hyrin.org
          </a>
          . If you are assessing AIC for an institutional data partnership and need something
          addressed formally, say so and we will respond in writing.
        </p>
      </section>

      <nav className="mt-10 border-t border-slate-100 pt-6">
        <p className="text-sm font-semibold text-slate-500">Related</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {GOVERNANCE.filter((o) => o.slug !== doc.slug).map((o) => (
            <Link
              key={o.slug}
              href={`/governance/${o.slug}`}
              className="badge bg-slate-100 text-slate-600 hover:bg-slate-200"
            >
              {o.title}
            </Link>
          ))}
          <Link href="/privacy" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Privacy Policy
          </Link>
          <Link href="/terms" className="badge bg-slate-100 text-slate-600 hover:bg-slate-200">
            Terms of Service
          </Link>
        </div>
      </nav>
    </div>
  );
}
