/**
 * Audience-facing descriptions of what the platform does for each user type.
 *
 * Kept as data rather than hand-written pages so the index, the individual
 * pages, the navigation and the sitemap can never describe the offering
 * differently. Every capability listed maps to something that actually ships —
 * no roadmap items presented as current features.
 */
export interface Solution {
  slug: string;
  audience: string;
  title: string;
  summary: string;
  /** Concrete problems this audience brings to the platform. */
  needs: string[];
  /** What AIC does about them, each tied to a shipped product. */
  capabilities: { name: string; product: string; href: string; description: string }[];
  /** A realistic worked example, not a hypothetical. */
  example: { title: string; steps: string[] };
}

export const SOLUTIONS: Solution[] = [
  {
    slug: "government",
    audience: "Governments & national statistical offices",
    title: "AIC for Governments",
    summary:
      "Turn national statistics and household surveys into monitoring dashboards, targeting analysis and reporting — without procuring separate statistical software.",
    needs: [
      "Poverty and welfare estimates disaggregated below the national average",
      "Evidence for geographic targeting of programmes and transfers",
      "SDG and national development plan reporting",
      "Analytical capacity that does not depend on per-seat licences",
    ],
    capabilities: [
      {
        name: "District and province-level poverty estimates",
        product: "AIC Micro",
        href: "/microdata",
        description:
          "FGT poverty indices, Gini coefficients and welfare distributions computed from your own household survey, broken down by any geography or population group in the data.",
      },
      {
        name: "Geographic targeting and hotspot detection",
        product: "AIC Geo",
        href: "/microdata/explorer",
        description:
          "Choropleth maps with Moran's I and LISA cluster analysis identify where deprivation concentrates, using administrative boundaries sourced automatically.",
      },
      {
        name: "SDG and development plan monitoring",
        product: "AIC SDG",
        href: "/sdg",
        description:
          "Progress against all 17 goals with indicator-level detail, comparable across the continent and over time.",
      },
      {
        name: "Macroeconomic context",
        product: "AIC Macro",
        href: "/dashboard",
        description:
          "GDP, inflation, debt, trade and social indicators harmonized for comparison with regional peers.",
      },
    ],
    example: {
      title: "Targeting a social protection programme",
      steps: [
        "Upload the national household survey (Stata, SPSS, CSV or a zipped archive).",
        "Map the survey's own column names to standard concepts — welfare, weights, district — once.",
        "Compute poverty headcount, gap and severity by district, survey-weighted.",
        "Render a choropleth and run Moran's I to find statistically significant clusters.",
        "Export the ranked district table and map for the programme design document.",
      ],
    },
  },
  {
    slug: "development-partners",
    audience: "Development partners & multilaterals",
    title: "AIC for Development Partners",
    summary:
      "Comparable, source-transparent evidence across countries and portfolios — with the provenance and methodology visible rather than assumed.",
    needs: [
      "Cross-country comparison on a consistent basis",
      "Baseline and monitoring indicators for programme design",
      "Transparency about where each number came from",
      "Analysis that partners in-country can reproduce",
    ],
    capabilities: [
      {
        name: "Cross-country comparison",
        product: "AIC Macro",
        href: "/countries",
        description:
          "Every African country with harmonized indicators, latest values and the years each series covers, so gaps are visible rather than hidden.",
      },
      {
        name: "Source transparency",
        product: "AIC Data",
        href: "/connectors",
        description:
          "46 catalogued sources with licence category, update frequency, access conditions and live health status for each.",
      },
      {
        name: "Household-level evidence",
        product: "AIC Micro",
        href: "/microdata",
        description:
          "Poverty, inequality, agriculture and livelihood diversification analysis on LSMS, DHS, MICS and national survey series.",
      },
      {
        name: "Reproducible analysis",
        product: "AIC Studio",
        href: "https://studio.hyrin.org",
        description:
          "Hosted Python and R notebooks so a method can be shared, rerun and audited rather than described in an annex.",
      },
    ],
    example: {
      title: "Scoping a regional agriculture programme",
      steps: [
        "Compare agricultural productivity and rainfall across candidate countries.",
        "Check which household surveys exist for each, and on what access terms.",
        "Analyse crop and income diversification where microdata is available.",
        "Share the notebook so country teams can rerun it on their own data.",
      ],
    },
  },
  {
    slug: "universities",
    audience: "Universities & research institutes",
    title: "AIC for Universities",
    summary:
      "A teaching and research environment where students run real econometrics on real African data — without a computer lab of licensed software.",
    needs: [
      "Statistical software students can use without per-seat licences",
      "African datasets that are actually reachable, with documented access terms",
      "A path from research question to method to analysis",
      "Reproducible work that supervisors can inspect",
    ],
    capabilities: [
      {
        name: "Econometrics workbench",
        product: "AIC Studio",
        href: "https://studio.hyrin.org",
        description:
          "Python and R in the browser with ARDL/NARDL, dynamic panel GMM, quantile regression, Bayesian VAR, spatial econometrics and DiD installed — and Stata and SPSS files read directly.",
      },
      {
        name: "Research workflow support",
        product: "AIC Research",
        href: "/research",
        description:
          "Literature search, theory and method recommendation, and variable suggestions, with sources cited.",
      },
      {
        name: "Survey discovery",
        product: "AIC Data",
        href: "/surveys",
        description:
          "Household and census microdata series across Africa with access conditions and documentation links.",
      },
      {
        name: "Applied analysis",
        product: "AIC Micro",
        href: "/microdata",
        description:
          "Poverty and welfare analytics students can run on a survey without writing the estimator themselves.",
      },
    ],
    example: {
      title: "Supervising a masters dissertation",
      steps: [
        "Student narrows a research question and finds relevant literature.",
        "Identifies a suitable survey series and checks its access terms.",
        "Runs the analysis in a notebook — panel GMM, ARDL, or poverty decomposition.",
        "Supervisor opens the same notebook and reruns it to verify the results.",
      ],
    },
  },
  {
    slug: "researchers",
    audience: "Independent researchers & analysts",
    title: "AIC for Researchers",
    summary:
      "The full analytical chain — discovery, data, method, estimation, interpretation — without assembling it from five disconnected tools.",
    needs: [
      "Finding which African data exists on a topic, and whether it is obtainable",
      "Running serious econometrics without a local software stack",
      "Moving between macro series and household microdata",
      "Producing outputs that can go into a paper or brief",
    ],
    capabilities: [
      {
        name: "Full econometrics stack",
        product: "AIC Studio",
        href: "https://studio.hyrin.org",
        description:
          "ARDL/NARDL and bounds testing, dynamic panel GMM, quantile regression, VAR/VECM, GARCH, Bayesian VAR, spatial econometrics, DiD and synthetic control — in Python and R.",
      },
      {
        name: "Macro time series",
        product: "AIC Macro",
        href: "/dashboard",
        description:
          "Harmonized indicators for every African country with the coverage years shown per series.",
      },
      {
        name: "Microdata analysis",
        product: "AIC Micro",
        href: "/microdata",
        description:
          "Upload a survey and compute poverty, inequality, agriculture and diversification measures with survey weights applied.",
      },
      {
        name: "Spatial analysis",
        product: "AIC Geo",
        href: "/microdata/explorer",
        description:
          "Moran's I, LISA clusters and choropleth output at district or province level.",
      },
    ],
    example: {
      title: "An inflation pass-through paper",
      steps: [
        "Pull the country's macro series and check coverage years.",
        "Estimate an ARDL model with bounds testing in the Studio.",
        "Test asymmetry with a NARDL specification.",
        "Export tables and figures for the manuscript.",
      ],
    },
  },
  {
    slug: "ngos",
    audience: "NGOs & civil society",
    title: "AIC for NGOs & Civil Society",
    summary:
      "Evidence for programme design, targeting and advocacy — at a level of rigour usually out of reach without a dedicated research unit.",
    needs: [
      "Knowing where need is concentrated, not just national averages",
      "Baseline figures for proposals and reporting",
      "Credible numbers with a citable source",
      "Analysis without hiring a statistician",
    ],
    capabilities: [
      {
        name: "Where need concentrates",
        product: "AIC Geo",
        href: "/microdata/explorer",
        description:
          "District-level poverty mapping with statistically tested clustering, so targeting rests on evidence rather than impression.",
      },
      {
        name: "Baseline indicators",
        product: "AIC Macro",
        href: "/countries",
        description:
          "Country pages with poverty, health, education, electricity access and employment figures, each with its source year.",
      },
      {
        name: "Development goal alignment",
        product: "AIC SDG",
        href: "/sdg",
        description:
          "Map programme outcomes to specific SDG indicators for funder reporting.",
      },
      {
        name: "Survey evidence",
        product: "AIC Micro",
        href: "/microdata",
        description:
          "Analyse an existing household survey rather than commissioning new collection.",
      },
    ],
    example: {
      title: "Writing a funding proposal",
      steps: [
        "Pull current poverty, education and electricity access figures for the country.",
        "Identify the districts where deprivation clusters.",
        "Tie the intended outcomes to specific SDG indicators.",
        "Cite the underlying source and year for every figure used.",
      ],
    },
  },
  {
    slug: "business",
    audience: "Business & investors",
    title: "AIC for Business & Investors",
    summary:
      "Market and macro context for African decisions, grounded in official statistics with the provenance visible.",
    needs: [
      "Comparable macro context across candidate markets",
      "Consumption and household structure, not just GDP",
      "Understanding where data is thin before relying on it",
      "Programmatic access for internal systems",
    ],
    capabilities: [
      {
        name: "Market comparison",
        product: "AIC Macro",
        href: "/countries",
        description:
          "GDP, growth, inflation, trade, debt, population and electricity access side by side across markets.",
      },
      {
        name: "Household demand",
        product: "AIC Micro",
        href: "/consumption",
        description:
          "Consumption patterns and welfare distributions from household survey data.",
      },
      {
        name: "Forward view",
        product: "AIC Forecast",
        href: "/forecast",
        description: "Projections and scenarios built on the underlying series.",
      },
      {
        name: "Programmatic access",
        product: "AIC API",
        href: "/docs",
        description:
          "A documented REST API so the same data can feed internal models and dashboards.",
      },
    ],
    example: {
      title: "Comparing entry markets",
      steps: [
        "Compare growth, inflation and trade openness across candidate countries.",
        "Check consumption structure where household survey data exists.",
        "Note which indicators are thin or dated before weighting them.",
        "Pull the same series through the API into an internal model.",
      ],
    },
  },
];

export function getSolution(slug: string) {
  return SOLUTIONS.find((s) => s.slug === slug);
}
