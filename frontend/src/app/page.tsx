import Link from "next/link";

const STATS = [
  { title: "54 Countries", desc: "Full African Union coverage — from Algeria to Zimbabwe" },
  { title: "27+ Indicators", desc: "GDP, inflation, poverty, trade, health, education, environment & more" },
  { title: "30 Years", desc: "Historical World Bank data covering 1995–2025" },
  { title: "AI-Powered", desc: "Automated, data-driven interpretation and policy analysis" },
];

const FEATURES = [
  { title: "Macro Dashboard", desc: "Combine multiple indicators on one chart, download data, and get instant AI interpretation.", href: "/dashboard" },
  { title: "SDG Analytics", desc: "Track all 17 Sustainable Development Goals with real indicator series, including rainfall and agricultural productivity.", href: "/sdg" },
  { title: "Microdata & Surveys", desc: "Browse survey and microdata catalogs from trusted statistical agencies.", href: "/surveys" },
  { title: "AI Research Assistant", desc: "Ask questions and get evidence-based answers grounded in real African datasets.", href: "/research" },
  { title: "Data Connectors", desc: "Live connections to World Bank, UN SDG, WHO and other reliable open data sources.", href: "/connectors" },
  { title: "Source Health", desc: "Monitor the freshness and reliability of every connected data source.", href: "/health" },
];

const GOALS = [
  {
    title: "Vision",
    desc: "A future where every policymaker, researcher, and citizen across Africa has instant access to trustworthy data and AI-powered insight to drive better decisions.",
  },
  {
    title: "Mission",
    desc: "To unify open macroeconomic, social, and environmental data from Africa's 54 countries into one reliable, transparent, and easy-to-use intelligence platform.",
  },
  {
    title: "Goals",
    desc: "Expand data coverage, deepen AI-driven analysis, and make evidence-based policymaking the norm across every African government and institution.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero */}
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center w-full bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-3xl">
          <div className="mb-6 flex justify-center gap-2">
            <span className="w-3 h-10 rounded bg-aic-green" />
            <span className="w-3 h-10 rounded bg-aic-gold" />
            <span className="w-3 h-10 rounded bg-aic-red" />
          </div>
          <h1 className="text-5xl font-bold text-aic-dark mb-4">
            African Intelligence Cloud
          </h1>
          <p className="text-xl text-aic-muted mb-8">
            Macroeconomic data, analytics, and policy intelligence for Africa.
            Powered by World Bank data across 54 countries, with AI-enhanced insights.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/dashboard"
              className="px-6 py-3 bg-aic-green text-white font-semibold rounded-lg hover:bg-green-800 transition"
            >
              Open Dashboard
            </Link>
            <Link
              href="/sdg"
              className="px-6 py-3 border-2 border-aic-green text-aic-green font-semibold rounded-lg hover:bg-green-50 transition"
            >
              Explore SDGs
            </Link>
          </div>
          <div className="mt-16 grid grid-cols-1 sm:grid-cols-4 gap-6 text-left">
            {STATS.map((card) => (
              <div key={card.title} className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
                <h3 className="font-bold text-aic-green text-lg mb-2">{card.title}</h3>
                <p className="text-aic-muted text-sm">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="w-full bg-white px-4 py-20">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-aic-dark mb-3">What you can do on AIC</h2>
          <p className="text-aic-muted mb-12 max-w-2xl mx-auto">
            One platform bringing together macroeconomic data, SDG tracking, microdata, and AI research tools.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <Link
                key={f.title}
                href={f.href}
                className="block text-left bg-slate-50 hover:bg-slate-100 transition rounded-xl p-6 border border-slate-100"
              >
                <h3 className="font-bold text-aic-dark mb-2">{f.title}</h3>
                <p className="text-sm text-aic-muted">{f.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Vision / Mission / Goals */}
      <div className="w-full bg-slate-900 text-white px-4 py-20">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-3">Our Vision, Mission &amp; Goals</h2>
          <p className="text-slate-300 mb-12 max-w-2xl mx-auto">
            Why the African Intelligence Cloud exists, and what it is working toward.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {GOALS.map((g) => (
              <div key={g.title} className="bg-slate-800 rounded-xl p-6 text-left border border-slate-700">
                <h3 className="font-bold text-aic-gold text-lg mb-2">{g.title}</h3>
                <p className="text-sm text-slate-300">{g.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Director profile */}
      <div className="w-full bg-white px-4 py-20">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-aic-dark mb-10 text-center">About the Director</h2>
          <div className="flex flex-col sm:flex-row items-center gap-8 bg-slate-50 rounded-2xl p-8 border border-slate-100">
            <div className="w-28 h-28 rounded-full bg-aic-green text-white flex items-center justify-center text-4xl font-bold shrink-0">
              LA
            </div>
            <div>
              <h3 className="text-xl font-bold text-aic-dark">Dr. Luqman Afolabi</h3>
              <p className="text-aic-green font-semibold text-sm mb-3">Founder &amp; Director, African Intelligence Cloud</p>
              <p className="text-aic-muted text-sm leading-relaxed">
                Dr. Luqman Afolabi is the founder and director of the African Intelligence Cloud, the brain
                behind the platform&apos;s vision of open, reliable, and AI-enhanced data intelligence for Africa.
                He leads the platform&apos;s strategy for expanding data coverage, strengthening analytical
                tools, and making evidence-based policymaking accessible to governments, researchers, and
                institutions across the continent.
              </p>
              <p className="text-sm mt-3">
                <a href="mailto:aluqman@hyrin.org" className="text-aic-green font-semibold hover:underline">
                  aluqman@hyrin.org
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
