import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Crop Forecasting — Yield & Production Projections for Africa",
  description:
    "Forecast African crop yield and production with confidence intervals using ARIMA, Holt exponential smoothing, linear trend and ensemble models, built on HarvestStat-Africa data.",
  keywords: [
    "crop yield forecast Africa", "agricultural forecasting", "ARIMA crop yield",
    "production forecast", "food security forecasting", "time series forecast agriculture",
    "maize yield forecast", "ensemble forecast crops",
  ],
  alternates: { canonical: "/forecast" },
  openGraph: {
    title: "Crop Forecasting — Yield & Production Projections for Africa",
    description: "Project African crop indicators forward with confidence intervals and multiple forecasting methods.",
    url: "/forecast",
    type: "website",
  },
};

export default function ForecastLayout({ children }: { children: React.ReactNode }) {
  return children;
}
