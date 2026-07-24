import type { Metadata } from "next";
import Link from "next/link";
import Logo from "@/components/ui/Logo";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "African Intelligence Cloud (AIC) is an AI-powered African research and policy intelligence platform integrating data discovery, microdata analytics, spatial intelligence, and AI-assisted research for Africa.",
};

const CHALLENGES = [
  {
    title: "Fragmented data ecosystems",
    desc: "Integrating macroeconomic, microdata, geospatial, and research resources through a unified platform.",
  },
  {
    title: "Limited analytical capacity",
    desc: "Enabling researchers to conduct advanced statistical and spatial analyses directly in the browser without requiring expensive proprietary software.",
  },
  {
    title: "Disconnected research workflows",
    desc: "Combining data access, analysis, visualization, AI-assisted interpretation, and reporting within one environment.",
  },
  {
    title: "Poor policy translation",
    desc: "Automatically transforming analytical outputs into evidence-based policy briefs, visual dashboards, and executive summaries.",
  },
  {
    title: "Limited interoperability",
    desc: "Harmonizing datasets from multiple countries using standardized metadata and common analytical frameworks.",
  },
  {
    title: "Barriers to collaboration",
    desc: "Providing secure cloud workspaces where multidisciplinary teams can work on shared projects regardless of location.",
  },
];

const PILLARS = [
  {
    number: "1",
    title: "African Data Intelligence",
    body: "AIC connects authoritative datasets from international and national sources, including macroeconomic indicators, household surveys, administrative statistics, climate information, health statistics, education indicators, trade databases, and research publications. Rather than requiring users to search multiple websites, AIC provides a unified discovery and integration environment.",
  },
  {
    number: "2",
    title: "Cloud-Based Microdata Analytics",
    body: "Researchers can securely upload licensed household survey datasets — including EICV, UNPS, DHS, LSMS, MICS, Afrobarometer, and other national surveys — and analyse them directly within the platform. Analyses include poverty measurement, inequality analysis, household welfare, nutrition, labour markets, agricultural productivity, impact evaluation, survey-weighted econometrics, and spatial statistics. Raw microdata remain protected while only authorized users access sensitive information.",
  },
  {
    number: "3",
    title: "Spatial Development Intelligence",
    body: "AIC integrates Geographic Information Systems (GIS) with socioeconomic analysis to support interactive mapping across African countries — visualizing poverty hotspots, district and provincial rankings, SDG performance, service accessibility, climate vulnerability, agricultural productivity, infrastructure distribution, and regional inequalities. This enables policymakers to identify where interventions are most needed rather than relying solely on national averages.",
  },
  {
    number: "4",
    title: "AI-Assisted Research",
    body: 'Artificial intelligence is embedded throughout the research workflow. Users can ask questions in natural language, such as "Which districts have the highest multidimensional poverty?" or "Estimate the determinants of poverty using a logistic regression model." The platform automatically generates statistical code, executes analyses, interprets findings, creates visualizations, and drafts publication-quality reports while maintaining transparency regarding methods and data sources.',
  },
];

const AUDIENCE = [
  "Universities and research institutes",
  "National statistical offices",
  "Government ministries",
  "Development partners",
  "International organizations",
  "Think tanks",
  "Civil society organizations",
  "Students and early-career researchers",
  "Independent policy analysts",
];

// Leadership team — sourced from the parent organization, HYRIN (Holistic Youth
// Resilience & Innovation Network), a CAC-registered Nigerian non-profit
// (RC 8729824). Each profile is publicly verifiable at https://hyrin.org.
const TEAM = [
  {
    initials: "LA",
    name: "Dr. Luqman O. Afolabi",
    role: "Founder & Director",
    credentials: "Ph.D. International Economics & Development",
    bio: "Architect of the AIC platform and the HYRIN integrated development model. 30+ peer-reviewed publications in development economics, poverty, and applied econometrics.",
    email: "aluqman@hyrin.org",
  },
  {
    initials: "YA",
    name: "Dr. Yusuf Hammed Agboola",
    role: "Lead Development Economist",
    credentials: "Ph.D. International Economics",
    bio: "15 years of expertise in programme economics, labour-market analysis, and development finance across West Africa.",
  },
  {
    initials: "AS",
    name: "Dr. Abdulmalik O. Salau",
    role: "Director of Financial Governance",
    credentials: "CPA Australia · Ph.D. & MSc Accounting",
    bio: "Oversees financial controls, audit readiness, and donor compliance to international NGO governance standards.",
  },
  {
    initials: "AG",
    name: "Azeezat Gbadamosi",
    role: "Public Health & Impact Monitoring",
    credentials: "M.Sc. Public Health",
    bio: "5+ years in health programme monitoring and community-based impact evaluation across Nigerian NGO and government health systems.",
  },
  {
    initials: "TO",
    name: "Dr. Toluwalope Ogunro",
    role: "Senior Advisor, Environmental Health",
    credentials: "Ph.D. Environmental & Public Health",
    bio: "Horizon 2020 researcher. Leads the green economy and climate-resilience strategy across the Oke-Ogun corridor.",
  },
];

const HYRIN_URL = "https://hyrin.org";

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-aic-hero px-4 pb-16 pt-20 sm:pt-24">
        <div className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-aic-green/10 blur-3xl animate-float" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-64 w-64 rounded-full bg-aic-gold/10 blur-3xl" />

        <div className="relative mx-auto max-w-3xl text-center">
          <div className="mb-6 flex justify-center animate-fade-in">
            <Logo size="lg" />
          </div>
          <p className="section-label animate-fade-in">About us</p>
          <h1 className="mt-2 animate-fade-in-up text-4xl font-bold tracking-tight text-aic-dark sm:text-5xl">
            African Intelligence Cloud (AIC)
          </h1>
          <p
            className="mx-auto mt-4 max-w-2xl animate-fade-in-up text-lg italic text-aic-muted"
            style={{ animationDelay: "0.1s" }}
          >
            Reimagining African Research Through AI, Data and Policy Intelligence
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl space-y-16 px-4 pb-20">
        {/* Intro */}
        <section className="card space-y-4 p-8 leading-relaxed text-slate-700">
          <p>
            Africa possesses one of the fastest-growing ecosystems of development data in the
            world. Governments, national statistical offices, universities, development partners,
            and international organizations have invested heavily in producing household surveys,
            censuses, administrative records, satellite data, and macroeconomic statistics.
            Valuable resources such as the Rwanda Integrated Household Living Conditions Survey
            (EICV), Uganda National Panel Survey (UNPS), Demographic and Health Surveys (DHS),
            Living Standards Measurement Study (LSMS), Multiple Indicator Cluster Surveys (MICS),
            and thousands of national statistical publications provide an unprecedented foundation
            for evidence-based policymaking.
          </p>
          <p>
            Despite this abundance of data, Africa continues to face a significant research
            utilization gap. Data are dispersed across numerous institutions, stored in
            incompatible formats, governed by different licensing arrangements, and often require
            advanced statistical software and technical expertise to analyse. Researchers
            frequently spend more time locating, cleaning, harmonizing, and integrating datasets
            than generating evidence. Policymakers, on the other hand, often lack access to timely,
            reproducible analyses that translate complex datasets into actionable insights.
          </p>
          <p>
            At the same time, advances in artificial intelligence, cloud computing, geospatial
            technologies, and open science have transformed research practices globally. Yet few
            platforms have been purpose-built to harness these innovations within the African
            context. Existing data portals primarily focus on data dissemination, while
            statistical software emphasizes analysis without integrated data access. AI assistants
            generate text but typically lack direct integration with trusted African datasets,
            household surveys, or policy workflows. Consequently, researchers must navigate
            multiple disconnected systems to complete a single study.
          </p>
        </section>

        {/* Gap AIC fills */}
        <section>
          <p className="section-label">Why AIC exists</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">The Gap African Intelligence Cloud Fills</h2>
          <p className="mt-3 leading-relaxed text-aic-muted">
            African Intelligence Cloud (AIC) was created to bridge this gap. Rather than serving
            as another data repository or dashboard, AIC is an AI-powered African research and
            policy intelligence platform that integrates data discovery, secure data management,
            statistical analysis, geospatial analytics, artificial intelligence, and collaborative
            research into a single cloud-based ecosystem.
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {CHALLENGES.map((c, i) => (
              <div
                key={c.title}
                className="card card-hover animate-fade-in-up p-5"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <h3 className="mb-1.5 font-semibold text-aic-green">{c.title}</h3>
                <p className="text-sm text-slate-500">{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What makes AIC different */}
        <section>
          <p className="section-label">Capabilities</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">What Makes AIC Different</h2>
          <p className="mt-3 leading-relaxed text-aic-muted">
            African Intelligence Cloud is designed specifically for African research priorities.
            The platform combines four complementary capabilities rarely available within a single
            system:
          </p>
          <div className="mt-8 space-y-4">
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
                  <h3 className="mb-1.5 font-semibold text-aic-dark">{p.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-500">{p.body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Built for */}
        <section className="card p-8">
          <p className="section-label">Community</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">Built for Africa&apos;s Research Community</h2>
          <div className="mt-6 flex flex-wrap gap-2">
            {AUDIENCE.map((a) => (
              <span key={a} className="badge bg-aic-green/10 text-aic-green">
                {a}
              </span>
            ))}
          </div>
          <p className="mt-6 text-sm leading-relaxed text-slate-500">
            The platform supports both teaching and professional research by reducing technical
            barriers while maintaining rigorous analytical standards.
          </p>
        </section>

        {/* Vision / Mission */}
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="rounded-2xl bg-aic-gradient p-8 text-white shadow-glow">
            <p className="text-xs font-bold uppercase tracking-widest text-aic-gold">Vision</p>
            <p className="mt-3 leading-relaxed text-white/85">
              To become Africa&apos;s leading AI-powered research and policy intelligence platform,
              enabling governments, researchers, and development partners to transform data into
              evidence, evidence into policy, and policy into sustainable development outcomes.
            </p>
          </div>
          <div className="rounded-2xl bg-aic-gradient p-8 text-white shadow-glow">
            <p className="text-xs font-bold uppercase tracking-widest text-aic-gold">Mission</p>
            <p className="mt-3 leading-relaxed text-white/85">
              To democratize access to high-quality African data, advanced analytics, geospatial
              intelligence, and artificial intelligence through a secure, collaborative cloud
              platform that strengthens research capacity and evidence-based decision-making
              across the continent.
            </p>
          </div>
        </section>

        {/* Long term ambition */}
        <section className="card p-8">
          <p className="section-label">Looking ahead</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">Our Long-Term Ambition</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            African Intelligence Cloud is more than a technology platform. It is a continental
            digital research infrastructure designed to support Africa&apos;s knowledge economy. By
            integrating trusted data sources, modern analytical methods, spatial intelligence, and
            artificial intelligence, AIC seeks to reduce the time between data collection and
            policy action, foster cross-country learning, strengthen institutional research
            capacity, and accelerate progress toward Africa&apos;s development priorities, including
            the African Union Agenda 2063 and the United Nations Sustainable Development Goals.
          </p>
          <p className="mt-4 leading-relaxed text-slate-600">
            Our objective is to ensure that every African researcher, policymaker, and institution
            has access to a modern, intelligent, and collaborative platform capable of producing
            timely, transparent, and actionable evidence for the continent&apos;s most pressing
            challenges.
          </p>
        </section>

        {/* Leadership team */}
        <section>
          <p className="section-label">Our people</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">Leadership Team</h2>
          <p className="mt-3 leading-relaxed text-aic-muted">
            AIC is delivered by a team combining rigorous academic training, international
            development expertise, and lived experience of the communities we serve. The platform is
            an initiative of{" "}
            <a
              href={HYRIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-aic-green underline underline-offset-4"
            >
              HYRIN — Holistic Youth Resilience &amp; Innovation Network
            </a>
            , a registered Nigerian non-profit (CAC RC&nbsp;8729824). Each profile below is publicly
            verifiable on the HYRIN website.
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {TEAM.map((m, i) => (
              <div
                key={m.name}
                className="card animate-fade-in-up flex gap-4 p-6"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-aic-green text-lg font-bold text-white">
                  {m.initials}
                </span>
                <div className="min-w-0">
                  <p className="font-semibold text-aic-dark">{m.name}</p>
                  <p className="text-sm font-medium text-aic-green">{m.role}</p>
                  <p className="mt-0.5 text-xs uppercase tracking-wide text-slate-400">
                    {m.credentials}
                  </p>
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
            <a
              href="https://twitter.com/hyrin_ng"
              target="_blank"
              rel="noopener noreferrer"
              className="badge bg-aic-green/10 text-aic-green"
            >
              HYRIN on X ↗
            </a>
            <span className="badge bg-slate-100 text-slate-500">
              CAC Registered NGO · RC 8729824
            </span>
            <span className="badge bg-slate-100 text-slate-500">Annual independent external audits</span>
          </div>
        </section>

        {/* Message from the Director */}
        <section className="card p-8">
          <p className="section-label">From the founder</p>
          <h2 className="mt-2 text-3xl font-bold text-aic-dark">Message from the Director</h2>
          <div className="mt-6 space-y-4 leading-relaxed text-slate-600">
            <p>Welcome to the African Intelligence Cloud (AIC).</p>
            <p>
              Africa stands at a pivotal moment in its development journey. Across the continent,
              governments, universities, national statistical offices, development partners, and
              research institutions are producing unprecedented volumes of high-quality data. Yet
              much of this valuable information remains fragmented, underutilized, and difficult
              to translate into timely policy decisions.
            </p>
            <p>The African Intelligence Cloud was established to bridge this gap.</p>
            <p>
              Our vision is to create Africa&apos;s leading AI-powered research and policy
              intelligence platform — one that enables researchers, policymakers, development
              practitioners, and innovators to seamlessly discover, integrate, analyse, visualize,
              and interpret data within a secure cloud environment.
            </p>
            <p>
              AIC is built on the belief that evidence should drive development. By combining
              trusted African datasets, advanced analytics, geospatial intelligence, artificial
              intelligence, and collaborative research tools, we aim to reduce the distance between
              data collection and policy action.
            </p>
            <p>
              The platform is designed to support a wide range of users, from students conducting
              their first empirical analysis to governments designing national development
              strategies, and from universities advancing scientific research to development
              partners monitoring programme impact.
            </p>
            <p>
              As AIC evolves, our ambition is to build a continental knowledge infrastructure that
              strengthens research capacity, promotes open and responsible data use, encourages
              collaboration across borders, and accelerates evidence-based decision-making
              throughout Africa.
            </p>
            <p>
              We invite researchers, institutions, governments, development organizations, and
              technology partners to join us in building a future where African data generates
              African solutions for African challenges.
            </p>
            <p className="font-medium text-aic-dark">
              Together, we can transform data into knowledge, knowledge into policy, and policy
              into sustainable development.
            </p>
          </div>

          <div className="mt-8 flex items-center gap-4 border-t border-slate-100 pt-6">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-aic-green text-xl font-bold text-white">
              LA
            </span>
            <div>
              <p className="font-semibold text-aic-dark">Dr. Luqman Afolabi</p>
              <p className="text-sm text-slate-500">Founder &amp; Director, African Intelligence Cloud (AIC)</p>
              <a href="mailto:aluqman@hyrin.org" className="text-sm text-aic-green hover:underline">
                aluqman@hyrin.org
              </a>
            </div>
          </div>
        </section>
      </div>

      {/* CTA band */}
      <section className="bg-aic-gradient px-6 py-16">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-5 text-center">
          <h2 className="text-3xl font-bold text-white">Ready to explore the data?</h2>
          <p className="max-w-xl text-white/80">
            Join the growing community of researchers and institutions using AIC to turn African
            data into evidence and evidence into policy.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/register" className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-aic-dark shadow-glow transition hover:bg-slate-100">
              Create free account
            </Link>
            <Link href="/dashboard" className="rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
              Open Dashboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
