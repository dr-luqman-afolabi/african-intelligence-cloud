/**
 * Trust and governance pages.
 *
 * Institutions handling household microdata ask these questions before they
 * share anything, and a platform that cannot answer them in writing does not
 * get the data. Content is deliberately specific about what the platform does
 * today — where something is a commitment rather than a shipped control, it
 * says so, because a governance page that overstates is worse than none.
 */
export interface GovernanceSection {
  heading: string;
  body: string[];
  /** Rendered as a checked list where the points are concrete controls. */
  points?: string[];
}

export interface GovernanceDoc {
  slug: string;
  title: string;
  summary: string;
  sections: GovernanceSection[];
}

export const GOVERNANCE: GovernanceDoc[] = [
  {
    slug: "data-governance",
    title: "Data Governance",
    summary:
      "How data enters the platform, who can reach it, and what happens to it — covering both public sources and microdata you upload.",
    sections: [
      {
        heading: "Two classes of data, handled differently",
        body: [
          "AIC holds two kinds of data and does not mix them. Public statistical data — World Bank, WHO, FAO, DHS Program, HDX, IPUMS and national statistical offices — is aggregated, openly licensed and served to anyone. Microdata you upload is private, access-controlled, and never redistributed or added to any public dataset.",
        ],
      },
      {
        heading: "Uploaded microdata",
        body: [
          "Uploaded survey files are written to private object storage bound to the uploading account. They are not listed publicly, not indexed, and not shared with other users unless you explicitly grant access.",
        ],
        points: [
          "Stored in access-controlled cloud storage, not on the public web",
          "Reachable only with a valid token belonging to the owning account",
          "Never redistributed, resold, or added to public catalogues",
          "Deletable on request, together with derived analysis artefacts",
        ],
      },
      {
        heading: "Licensing and attribution of public data",
        body: [
          "Public data carries the licence of its original provider. AIC does not relicense it. Each catalogued source records its licence category, access conditions, update frequency and whether redistribution or registration is required — visible in the data source catalogue rather than buried in terms.",
          "Where a source requires registration or approval before use, AIC links you to the provider rather than proxying the restricted data.",
        ],
      },
      {
        heading: "Re-identification",
        body: [
          "Household survey microdata is de-identified by its producers, but de-identification is not absolute. Attempting to re-identify individuals or households in any dataset accessed through AIC is prohibited under the terms of service, and analysis outputs should be reported at a level of aggregation that does not expose individual records.",
        ],
      },
    ],
  },
  {
    slug: "security",
    title: "Security",
    summary:
      "The controls protecting accounts, uploaded data and the platform itself — stated specifically rather than as reassurance.",
    sections: [
      {
        heading: "Accounts and access",
        body: [
          "Authentication uses signed bearer tokens; passwords are stored only as bcrypt hashes and are never recoverable in plain text. New accounts require administrator approval before they can sign in, so access is granted rather than self-issued.",
        ],
        points: [
          "Passwords hashed with bcrypt — never stored or logged in plain text",
          "Administrator approval required before a new account becomes active",
          "Role-based permissions separating viewers, analysts and administrators",
          "Administrative and data-modifying endpoints require an authenticated administrator",
        ],
      },
      {
        heading: "Transport and storage",
        body: [
          "All traffic is served over HTTPS with certificates renewed automatically. The application database is managed, encrypted at rest, and reachable only over a private connection — it is not exposed to the public internet. Uploaded files are held in private cloud storage under the same access controls.",
        ],
      },
      {
        heading: "Platform hardening",
        body: [
          "Public AI endpoints are rate-limited per client to prevent abuse. Cross-origin access is restricted to the platform's own front end. In production the interactive API explorer and machine-readable schema are disabled, so the endpoint surface is not published.",
        ],
      },
      {
        heading: "Reporting a vulnerability",
        body: [
          "If you believe you have found a security issue, email info.aic@hyrin.org with enough detail to reproduce it. Please do not disclose it publicly until it has been addressed. We will acknowledge and keep you informed of the outcome.",
        ],
      },
    ],
  },
  {
    slug: "responsible-ai",
    title: "Responsible AI",
    summary:
      "Where AI is used in the platform, what it is allowed to do, and where the limits are.",
    sections: [
      {
        heading: "What AI is used for",
        body: [
          "AI assists with interpretation and navigation, not with producing the numbers. Statistical results — poverty indices, inequality measures, spatial statistics, econometric estimates — are computed by deterministic, inspectable code. Language models are used to describe results in prose, suggest relevant literature, theories, methods and variables, and translate natural-language questions into analysis parameters.",
        ],
      },
      {
        heading: "What AI is not used for",
        body: [
          "No figure shown on the platform is generated by a language model. AI does not estimate, impute or invent data points, and it does not decide statistical results.",
        ],
        points: [
          "Estimates come from published statistical methods, not from a model's prediction",
          "AI-generated text is presented as interpretation, distinguishable from computed output",
          "Where an AI service is unavailable, the platform falls back to deterministic logic rather than fabricating a response",
        ],
      },
      {
        heading: "Limitations you should assume",
        body: [
          "Language models can be confidently wrong. AI-generated interpretation, literature suggestions and method recommendations are a starting point for expert judgement, not a substitute for it. Verify citations before relying on them, and check that a recommended method suits your data before applying it.",
          "Analytical output reflects the data and parameters you supply. A poverty line, welfare variable or weighting choice that is wrong for the survey will produce a confident but meaningless result.",
        ],
      },
      {
        heading: "Your data and AI",
        body: [
          "Uploaded microdata is not used to train models. Where an analysis invokes an AI service, only the parameters and aggregate results needed for interpretation are sent — not raw household records.",
        ],
      },
    ],
  },
  {
    slug: "methodology",
    title: "Methodology",
    summary:
      "The statistical methods behind the platform's outputs, and the assumptions they carry.",
    sections: [
      {
        heading: "Poverty and inequality",
        body: [
          "Poverty is measured using the Foster–Greer–Thorbecke class: headcount ratio (FGT0), poverty gap (FGT1) and squared poverty gap (FGT2), computed against a poverty line you specify in the survey's own welfare units. Inequality is reported as the Gini coefficient. Where a survey weight variable is supplied it is applied throughout, so estimates are population-representative rather than sample averages.",
        ],
      },
      {
        heading: "Spatial statistics",
        body: [
          "Spatial autocorrelation uses Moran's I with row-standardised Queen contiguity weights, computed via PySAL. Local clustering uses Local Moran's I (LISA), with quadrants reported as high-high, low-low, high-low and low-high; a unit is labelled a cluster only where the local statistic is significant at the 5% level. Administrative boundaries are sourced from geoBoundaries under CC-BY 4.0 where you do not supply your own.",
          "Moran's I and LISA require at least five matched geographic units; below that the platform reports the statistic as unavailable rather than computing something unstable.",
        ],
      },
      {
        heading: "Macroeconomic series",
        body: [
          "Country indicator series are harmonized from their providers and presented with the years each series actually covers, so gaps are visible rather than interpolated away. AIC does not impute missing observations or extend series beyond their source.",
        ],
      },
      {
        heading: "What we do not do",
        body: [
          "Estimates are not smoothed, back-cast or reconciled between sources. Where two providers disagree, the provenance of each figure is shown rather than a blended value presented as fact. Coverage varies by country, indicator and year according to what the source publishes.",
        ],
      },
    ],
  },
  {
    slug: "accessibility",
    title: "Accessibility",
    summary:
      "Our approach to making the platform usable for everyone, and where it currently falls short.",
    sections: [
      {
        heading: "Approach",
        body: [
          "AIC aims to meet WCAG 2.1 Level AA. The interface uses semantic HTML, keyboard-navigable controls, labelled form fields and colour combinations chosen for contrast against their backgrounds. Public pages are server-rendered, so content is available without waiting on client-side scripting.",
        ],
      },
      {
        heading: "Known limitations",
        body: [
          "We would rather state these than imply full conformance. Interactive charts convey information visually; where a chart is central to a page, the underlying values are also available as a table or export. Geographic maps are inherently visual, and ranked tables are provided alongside them. Formal third-party accessibility auditing has not yet been carried out.",
        ],
      },
      {
        heading: "Telling us about a barrier",
        body: [
          "If something on the platform prevents you from doing your work, email info.aic@hyrin.org describing what you were trying to do and what got in the way. Reports of specific barriers are more useful to us than general conformance statements, and we treat them as defects.",
        ],
      },
    ],
  },
];

export function getGovernanceDoc(slug: string) {
  return GOVERNANCE.find((d) => d.slug === slug);
}
