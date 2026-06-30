"use client";
import { useState } from "react";

interface NotebookTemplate {
  id: string;
  title: string;
  description: string;
  language: "python" | "r" | "stata";
  tags: string[];
  code: string;
}

const TEMPLATES: NotebookTemplate[] = [
  {
    id: "py-gdp-trend",
    title: "GDP Trend Analysis",
    description: "Fetch GDP data via the AIC API and plot trends for selected countries.",
    language: "python",
    tags: ["GDP", "economics", "matplotlib"],
    code: `import requests
import pandas as pd
import matplotlib.pyplot as plt

BASE = "http://localhost:8000/api/v1"

# Fetch data for Nigeria
resp = requests.get(f"{BASE}/macro-data", params={"country": "NGA"})
payload = resp.json()

df = pd.DataFrame(payload["data"])
gdp = df[df["indicator_code"] == "NY.GDP.MKTP.CD"].sort_values("year")

plt.figure(figsize=(10, 4))
plt.plot(gdp["year"], gdp["value"] / 1e9, marker="o")
plt.title("Nigeria GDP (current USD bn)")
plt.xlabel("Year"); plt.ylabel("USD Billions")
plt.tight_layout(); plt.show()
`,
  },
  {
    id: "r-inflation",
    title: "Inflation Time-Series (R)",
    description: "Pull CPI data and produce publication-ready ggplot2 chart.",
    language: "r",
    tags: ["CPI", "inflation", "ggplot2"],
    code: `library(httr)
library(jsonlite)
library(ggplot2)
library(dplyr)

BASE <- "http://localhost:8000/api/v1"

resp <- GET(paste0(BASE, "/macro-data"), query = list(country = "KEN"))
payload <- content(resp, as = "parsed", type = "application/json")

df <- bind_rows(payload$data) %>%
  filter(indicator_code == "FP.CPI.TOTL.ZG") %>%
  arrange(year)

ggplot(df, aes(x = year, y = value)) +
  geom_line(colour = "#16a34a", linewidth = 1.2) +
  geom_point() +
  labs(title = "Kenya: Annual CPI Inflation (%)",
       x = "Year", y = "Inflation (%)") +
  theme_minimal()
`,
  },
  {
    id: "stata-trade",
    title: "Trade Balance Analysis (Stata)",
    description: "Import AIC data using Python bridge and run regression in Stata.",
    language: "stata",
    tags: ["trade", "regression", "OLS"],
    code: `* AIC Stata Integration — requires Python 3 and the requests package
* Step 1: export data via Python bridge
python:
import requests, pandas as pd
resp = requests.get("http://localhost:8000/api/v1/macro-data",
                    params={"country": "ZAF"})
df = pd.DataFrame(resp.json()["data"])
df.to_csv("/tmp/aic_zaf.csv", index=False)
end

* Step 2: import and analyse
import delimited "/tmp/aic_zaf.csv", clear
keep if indicator_code == "BN.CAB.XOKA.CD"
destring value, replace
tsset year
tsline value, title("South Africa: Current Account Balance") ///
             ytitle("USD") xtitle("Year")
reg value year
`,
  },
  {
    id: "py-sdg-radar",
    title: "SDG Radar Chart",
    description: "Visualise SDG indicator availability as a radar/spider chart.",
    language: "python",
    tags: ["SDG", "radar", "plotly"],
    code: `import requests
import plotly.graph_objects as go

BASE = "http://localhost:8000/api/v1"
goals = requests.get(f"{BASE}/sdg/goals").json()

labels = [f"SDG {g['goal_number']}" for g in goals]
values = [len(g["indicators"]) for g in goals]
values += [values[0]]  # close the polygon

fig = go.Figure(go.Scatterpolar(
    r=values,
    theta=labels + [labels[0]],
    fill="toself",
    name="Indicator coverage",
    line_color="#16a34a",
))
fig.update_layout(
    polar=dict(radialaxis=dict(visible=True)),
    title="SDG Indicator Coverage in AIC",
)
fig.show()
`,
  },
];

const LANG_BADGE: Record<string, string> = {
  python: "bg-blue-100 text-blue-700",
  r: "bg-purple-100 text-purple-700",
  stata: "bg-orange-100 text-orange-700",
};

export default function NotebooksPage() {
  const [active, setActive] = useState<NotebookTemplate | null>(null);
  const [copied, setCopied] = useState(false);

  function copy(code: string) {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Notebook Templates</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Ready-to-run code snippets for Python, R, and Stata that connect to the AIC API
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-4">
          {/* Template list */}
          <div className="space-y-3">
            {TEMPLATES.map((t) => (
              <button
                key={t.id}
                onClick={() => setActive(t)}
                className={`w-full text-left bg-white rounded-xl border p-4 shadow-sm transition space-y-2 hover:border-aic-green ${
                  active?.id === t.id ? "border-aic-green ring-1 ring-aic-green" : "border-slate-200"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-800">{t.title}</p>
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full ${LANG_BADGE[t.language]}`}
                  >
                    {t.language}
                  </span>
                </div>
                <p className="text-xs text-slate-500">{t.description}</p>
                <div className="flex flex-wrap gap-1">
                  {t.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>

          {/* Code preview */}
          <div className="sticky top-4">
            {active ? (
              <div className="bg-slate-900 rounded-xl overflow-hidden shadow-lg">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                  <div>
                    <p className="text-sm font-semibold text-white">{active.title}</p>
                    <p className="text-xs text-slate-400">{active.language}</p>
                  </div>
                  <button
                    onClick={() => copy(active.code)}
                    className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 text-slate-200 hover:bg-slate-600 transition"
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <pre className="p-4 overflow-x-auto text-xs text-slate-300 font-mono leading-relaxed max-h-[60vh] overflow-y-auto">
                  <code>{active.code}</code>
                </pre>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 h-64 flex items-center justify-center text-slate-400 text-sm shadow-sm">
                Select a template to preview the code
              </div>
            )}
          </div>
        </div>

        {/* Setup instructions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <h2 className="text-sm font-bold text-slate-800">Setup</h2>
          <div className="grid md:grid-cols-3 gap-4 text-xs text-slate-600">
            <div className="space-y-1">
              <p className="font-semibold text-slate-700">Python</p>
              <pre className="bg-slate-50 rounded-lg p-2 font-mono text-[11px]">{`pip install requests pandas matplotlib plotly`}</pre>
            </div>
            <div className="space-y-1">
              <p className="font-semibold text-slate-700">R</p>
              <pre className="bg-slate-50 rounded-lg p-2 font-mono text-[11px]">{`install.packages(c("httr","jsonlite","ggplot2","dplyr"))`}</pre>
            </div>
            <div className="space-y-1">
              <p className="font-semibold text-slate-700">Stata</p>
              <pre className="bg-slate-50 rounded-lg p-2 font-mono text-[11px]">{`* Requires Stata 16+ with Python integration\npython set exec python3, perm`}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
