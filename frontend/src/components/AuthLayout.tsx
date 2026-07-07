import Logo from "@/components/ui/Logo";

const HIGHLIGHTS = [
  "Upload household surveys and compute poverty & inequality indices instantly",
  "Africa-wide GIS choropleth maps with Moran's I and LISA cluster analysis",
  "30 years of macroeconomic data across every African country",
];

export default function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="grid min-h-[calc(100vh-4rem)] lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-aic-gradient p-10 text-white lg:flex">
        <div className="pointer-events-none absolute -top-16 -right-16 h-72 w-72 rounded-full bg-white/10 blur-3xl animate-float" />
        <div className="relative">
          <Logo size="md" />
        </div>
        <div className="relative space-y-6">
          <h2 className="text-3xl font-bold leading-tight">
            Policy intelligence, built for Africa
          </h2>
          <ul className="space-y-3">
            {HIGHLIGHTS.map((h) => (
              <li key={h} className="flex items-start gap-2.5 text-sm text-white/85">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="mt-0.5 shrink-0">
                  <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {h}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-white/50">© {new Date().getFullYear()} African Intelligence Cloud</p>
      </div>

      <div className="flex items-center justify-center bg-slate-50 px-4 py-12">
        <div className="w-full max-w-md animate-fade-in-up">
          <div className="card p-8">
            <div className="mb-6 text-center lg:text-left">
              <div className="mb-4 flex justify-center lg:hidden">
                <Logo />
              </div>
              <h1 className="text-2xl font-bold text-aic-dark">{title}</h1>
              <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
            </div>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
