/**
 * Shared About content.
 *
 * The About page had grown into several essays on one URL — background,
 * problem, differentiation, community, vision, ambition, team and a director's
 * message. Splitting it across pages means each needs the same underlying
 * content, so it lives here rather than being duplicated per page.
 */
export const HYRIN_URL = "https://hyrin.org";

export const CHALLENGES = [
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

export const PILLARS = [
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

export const AUDIENCE = [
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
export const TEAM = [
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
