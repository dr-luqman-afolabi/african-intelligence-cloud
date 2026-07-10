"use client";

import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { ForecastResponse } from "@/lib/api";

export default function ForecastChart({
  data,
  model,
  height = 380,
}: {
  data: ForecastResponse;
  model: string;
  height?: number;
}) {
  const hist = data.history || [];
  const fc = data.models?.[model]?.points || [];
  const units = data.units || "";

  const rows: any[] = [];
  for (const h of hist) rows.push({ year: h.year, hist: h.value });
  if (hist.length && fc.length) {
    rows[rows.length - 1].fcast = hist[hist.length - 1].value;
    rows[rows.length - 1].range = [hist[hist.length - 1].value, hist[hist.length - 1].value];
  }
  for (const p of fc) rows.push({ year: p.year, fcast: p.value, range: [p.lower, p.upper] });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
        <XAxis dataKey="year" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} label={{ value: units, angle: -90, position: "insideLeft", style: { fontSize: 12, fill: "#64748b" } }} />
        <Tooltip formatter={(v: any) => (Array.isArray(v) ? `${v[0]} – ${v[1]}` : v)} />
        <Legend />
        <Area type="monotone" dataKey="range" name="95% interval" stroke="none" fill="#10b981" fillOpacity={0.15} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="hist" name="Historical" stroke="#0f766e" strokeWidth={2} dot={false} connectNulls />
        <Line type="monotone" dataKey="fcast" name="Forecast" stroke="#10b981" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 2 }} connectNulls />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
