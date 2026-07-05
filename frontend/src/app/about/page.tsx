import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "Learn about African Intelligence Cloud's vision and mission to power evidence-based decisions across Africa with open macro and microdata, dashboards, and AI-assisted research tools.",
};

const VALUES = [
  {
    title: "Open by default",
    body: "We connect to trusted public sources such as World Bank, FAOSTAT, and national statistics offices, and make the resulting data easy to explore, chart, and download.",
  },
  {
    title: "Built for researchers",
    body: "Literature review, method advisory, and citation tools sit alongside the data, so analysts can move from question to evidence without switching tools.",
  },
  {
    title: "Reliable infrastructure",
    body: "Continuous health checks, monitoring, and automated deployment keep every connector and dashboard dependable for day-to-day policy and research work.",
  },
];

export default function AboutPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-14">
        <div className="flex justify-center gap-0.5 mb-4">
          <span className="w-3 h-10 rounded bg-aic-green" />
          <span className="w-3 h-10 rounded bg-aic-gold" />
          <span className="w-3 h-10 rounded bg-aic-red" />
        </div>
        <h1 className="text-4xl font-bold text-aic-dark mb-4">
          About African Intelligence Cloud
        </h1>
        <p className="text-xl text-aic-muted max-w-2xl mx-auto">
          A single home for African macrodata, microdata, dashboards, and AI-assisted
          research, built to help analysts, policymakers, and researchers find and
          understand evidence faster.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-14">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <h2 className="font-bold text-aic-green text-lg mb-2">Our Vision</h2>
          <p className="text-aic-muted text-sm leading-relaxed">
            A future where every policymaker, researcher, and citizen across Africa
            can find trustworthy data and turn it into clear, evidence-based decisions
            in minutes rather than weeks.
          </p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <h2 className="font-bold text-aic-green text-lg mb-2">Our Mission</h2>
          <p className="text-aic-muted text-sm leading-relaxed">
            To bring together macro and microdata, econometric tools, and AI-assisted
            research support in one reliable platform, so that good analysis is never
            blocked by scattered data or fragmented tooling.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
        {VALUES.map((v) => (
          <div key={v.title} className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
            <h3 className="font-bold text-aic-dark text-base mb-2">{v.title}</h3>
            <p className="text-aic-muted text-sm">{v.body}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
