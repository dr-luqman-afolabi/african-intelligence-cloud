import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
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
          Powered by World Bank data with AI-enhanced insights.
        </p>

        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-aic-green text-white font-semibold rounded-lg hover:bg-green-800 transition"
          >
            Open Dashboard
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 border-2 border-aic-green text-aic-green font-semibold rounded-lg hover:bg-green-50 transition"
          >
            API Docs
          </a>
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
          {[
            { title: "6 Countries", desc: "Nigeria, Rwanda, South Africa, Ghana, Kenya, Ethiopia" },
            { title: "8 Indicators", desc: "GDP, Inflation, Poverty, FDI, Debt, Trade, Unemployment" },
            { title: "30 Years", desc: "Historical data from World Bank covering 1995–2024" },
          ].map((card) => (
            <div key={card.title} className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
              <h3 className="font-bold text-aic-green text-lg mb-2">{card.title}</h3>
              <p className="text-aic-muted text-sm">{card.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
