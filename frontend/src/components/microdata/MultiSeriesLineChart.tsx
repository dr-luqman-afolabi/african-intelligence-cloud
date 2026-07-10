"use client";

import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface SeriesPoint {
  x: string;
  value: number;
}

export interface ChartSeries {
  label: string;
  points: SeriesPoint[];
}

interface Props {
  series: ChartSeries[];
  yLabel?: string;
  height?: number;
}

const COLORS = [
  "#006B3C", "#b45309", "#1d4ed8", "#be123c", "#4d7c0f",
  "#7c3aed", "#c2410c", "#0369a1", "#0f766e", "#9333ea",
];

// Sort categorical wave labels like "W1 2011-12" by embedded year then wave number.
function xSortKey(x: string): number {
  const year = /(\d{4})/.exec(x);
  const wave = /w\s*(\d+)/i.exec(x);
  return (year ? parseInt(year[1], 10) : 0) * 100 + (wave ? parseInt(wave[1], 10) : 0);
}

export default function MultiSeriesLineChart({ series, yLabel, height = 380 }: Props) {
  const { rows, keys } = useMemo(() => {
    const keys = series.map((s) => s.label);
    // Union of all x values across every series, globally ordered.
    const xs = Array.from(new Set(series.flatMap((s) => s.points.map((p) => p.x))));
    xs.sort((a, b) => xSortKey(a) - xSortKey(b));
    const byX: Record<string, Record<string, number | string>> = {};
    for (const x of xs) byX[x] = { x };
    for (const s of series) {
      for (const p of s.points) {
        byX[p.x][s.label] = p.value;
      }
    }
    return { rows: xs.map((x) => byX[x]), keys };
  }, [series]);

  if (series.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-aic-muted text-sm border border-dashed border-slate-300 rounded-lg">
        Choose a country and one or more indicators to plot them together.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="x" tick={{ fontSize: 11 }} angle={-15} textAnchor="end" height={54} />
        <YAxis
          tick={{ fontSize: 11 }}
          label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", style: { fontSize: 11 } } : undefined}
        />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {keys.map((k, i) => (
          <Line
            key={k}
            type="monotone"
            dataKey={k}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2.5}
            dot={{ r: 3 }}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
