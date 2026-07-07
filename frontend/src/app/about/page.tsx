import type { Metadata } from "next";

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

export default function AboutPage() {
  return (
    <main className="px-4 py-16">
      <div className="max-w-4xl mx-auto space-y-14">
        {/* Header */}
        <div className="text-center">
          <div className="mb-5 flex justify-center gap-2">
            <span className="w-3 h-10 rounded bg-aic-green" />
            <span className="w-3 h-10 rounded bg-aic-gold" />
            <span className="w-3 h-10 rounded bg-aic-red" />
          </div>
          <h1 className="text-4xl font-bold text-aic-dark mb-3">
            About African Intelligence Cloud (AIC)
          </h1>
          <p className="text-lg text-aic-muted italic max-w-2xl mx-auto">
            Reimagining African Research Through AI, Data and Policy Intelligence
          </p>
        </div>

        {/* Intro */}
        <section className="bg-white rounded-xl border border-slate-100 shadow-sm p-8 space-y-4 text-slate-700 leading-relaxed">
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
          <h2 className="text-2xl font-bold text-aic-dark mb-2">The Gap African Intelligence Cloud Fills</h2>
          <p className="text-slate-700 mb-6 leading-relaxed">
            African Intelligence Cloud (AIC) was created to bridge this gap. Rather than serving
            as another data repository or dashboard, AIC is an AI-powered African research and
            policy intelligence platform that integrates data discovery, secure data management,
            statistical analysis, geospatial analytics, artificial intelligence, and collaborative
            research into a single cloud-based ecosystem.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {CHALLENGES.map((c) => (
              <div key={c.title} className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
                <h3 className="font-semibold text-aic-green mb-1.5">{c.title}</h3>
                <p className="text-sm text-slate-600">{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What makes AIC different */}
        <section>
          <h2 className="text-2xl font-bold text-aic-dark mb-2">What Makes AIC Different</h2>
          <p className="text-slate-700 mb-6 leading-relaxed">
            African Intelligence Cloud is designed specifically for African research priorities.
            The platform combines four complementary capabilities rarely available within a single
            system:
          </p>
          <div className="space-y-4">
            {PILLARS.map((p) => (
              <div key={p.number} className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 flex gap-4">
                <span className="shrink-0 w-10 h-10 rounded-full bg-aic-green text-white font-bold flex items-center justify-center">
                  {p.number}
                </span>
                <div>
                  <h3 className="font-bold text-aic-dark mb-1.5">{p.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{p.body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Built for */}
        <section className="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-aic-dark mb-4">Built for Africa&apos;s Research Community</h2>
          <div className="flex flex-wrap gap-2 mb-5">
            {AUDIENCE.map((a) => (
              <span key={a} className="text-sm px-3 py-1.5 rounded-full bg-slate-100 text-slate-700">
                {a}
              </span>
            ))}
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            The platform supports both teaching and professional research by reducing technical
            barriers while maintaining rigorous analytical standards.
          </p>
        </section>

        {/* Vision / Mission */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-aic-dark text-white rounded-xl p-8">
            <h2 className="text-xl font-bold mb-3 text-aic-gold">Vision</h2>
            <p className="text-slate-200 leading-relaxed">
              To become Africa&apos;s leading AI-powered research and policy intelligence platform,
              enabling governments, researchers, and development partners to transform data into
              evidence, evidence into policy, and policy into sustainable development outcomes.
            </p>
          </div>
          <div className="bg-aic-dark text-white rounded-xl p-8">
            <h2 className="text-xl font-bold mb-3 text-aic-gold">Mission</h2>
            <p className="text-slate-200 leading-relaxed">
              To democratize access to high-quality African data, advanced analytics, geospatial
              intelligence, and artificial intelligence through a secure, collaborative cloud
              platform that strengthens research capacity and evidence-based decision-making
              across the continent.
            </p>
          </div>
        </section>

        {/* Long term ambition */}
        <section className="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-aic-dark mb-4">Our Long-Term Ambition</h2>
          <p className="text-slate-700 leading-relaxed">
            African Intelligence Cloud is more than a technology platform. It is a continental
            digital research infrastructure designed to support Africa&apos;s knowledge economy. By
            integrating trusted data sources, modern analytical methods, spatial intelligence, and
            artificial intelligence, AIC seeks to reduce the time between data collection and
            policy action, foster cross-country learning, strengthen institutional research
            capacity, and accelerate progress toward Africa&apos;s development priorities, including
            the African Union Agenda 2063 and the United Nations Sustainable Development Goals.
          </p>
          <p className="text-slate-700 leading-relaxed mt-4">
            Our objective is to ensure that every African researcher, policymaker, and institution
            has access to a modern, intelligent, and collaborative platform capable of producing
            timely, transparent, and actionable evidence for the continent&apos;s most pressing
            challenges.
          </p>
        </section>

        {/* Message from the Director */}
        <section className="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-aic-dark mb-6">Message from the Director</h2>
          <div className="space-y-4 text-slate-700 leading-relaxed">
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

          <div className="mt-8 pt-6 border-t border-slate-100 flex items-center gap-4">
            <span className="w-14 h-14 rounded-full bg-aic-green text-white font-bold text-xl flex items-center justify-center shrink-0">
              LA
            </span>
            <div>
              <p className="font-bold text-aic-dark">Dr. Luqman Afolabi</p>
              <p className="text-sm text-slate-500">Founder &amp; Director, African Intelligence Cloud (AIC)</p>
              <a
                href="mailto:aluqman@hyrin.org"
                className="text-sm text-aic-green hover:underline"
              >
                aluqman@hyrin.org
              </a>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
