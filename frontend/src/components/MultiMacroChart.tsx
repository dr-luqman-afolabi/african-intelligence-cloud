"use client";

import { useMemo, useRef, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface ChartSeries {
  code: string;
  label: string;
  color: string;
  data: { year: number; value: number }[];
}

interface MultiMacroChartProps {
  series: ChartSeries[];
}

const COLORS = ["#0f766e", "#b45309", "#1d4ed8", "#be123c", "#4d7c0f", "#7c3aed", "#c2410c", "#0369a1"];

type ChartType = "line" | "bar";

export default function MultiMacroChart({ series }: MultiMacroChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [chartType, setChartType] = useState<ChartType>("line");

  const merged = useMemo(() => {
    const years = new Set<number>();
    series.forEach((s) => s.data.forEach((d) => years.add(d.year)));
    const sortedYears = Array.from(years).sort((a, b) => a - b);
    return sortedYears.map((year) => {
      const row: Record<string, number | null> = { year };
      series.forEach((s) => {
        const point = s.data.find((d) => d.year === year);
        row[s.code] = point ? point.value : null;
      });
      return row;
    });
  }, [series]);

  function downloadCSV() {
    if (merged.length === 0) return;
    const headers = ["year", ...series.map((s) => s.label)];
    const rows = merged.map((row) => [row.year, ...series.map((s) => row[s.code] ?? "")].join(","));
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "aic-macro-data.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function downloadPNG() {
    const svg = containerRef.current?.querySelector("svg");
    if (!svg) return;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const bbox = svg.getBoundingClientRect();
      canvas.width = bbox.width * 2;
      canvas.height = bbox.height * 2;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(2, 2);
      ctx.drawImage(img, 0, 0, bbox.width, bbox.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const pngUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = pngUrl;
        link.download = "aic-macro-chart.png";
        link.click();
        URL.revokeObjectURL(pngUrl);
      });
    };
    img.src = url;
  }

  if (series.length === 0) {
    return <div className="text-center text-aic-muted py-16">Select at least one indicator to view the chart.</div>;
  }

  return (
    <div>
      <div className="flex justify-end mb-3">
        <div className="inline-flex rounded-full bg-slate-100 p-1">
          <button
            onClick={() => setChartType("line")}
            className={
              chartType === "line"
                ? "px-3 py-1 rounded-full text-xs font-medium bg-aic-dark text-white transition"
                : "px-3 py-1 rounded-full text-xs font-medium text-slate-600 hover:text-aic-dark transition"
            }
          >
            Line
          </button>
          <button
            onClick={() => setChartType("bar")}
            className={
              chartType === "bar"
                ? "px-3 py-1 rounded-full text-xs font-medium bg-aic-dark text-white transition"
                : "px-3 py-1 rounded-full text-xs font-medium text-slate-600 hover:text-aic-dark transition"
            }
          >
            Bar
          </button>
        </div>
      </div>
      <div ref={containerRef}>
        <ResponsiveContainer width="100%" height={380}>
          {chartType === "line" ? (
            <LineChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }} data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="year" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} />
              <Tooltip />
              <Legend />
              {series.map((s, i) => (
                <Line
                  key={s.code}
                  type="monotone"
                  dataKey={s.code}
                  name={s.label}
                  stroke={s.color || COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          ) : (
            <BarChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }} data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="year" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} />
              <Tooltip />
              <Legend />
              {series.map((s, i) => (
                <Bar
                  key={s.code}
                  dataKey={s.code}
                  name={s.label}
                  fill={s.color || COLORS[i % COLORS.length]}
                />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <div className="flex gap-3 mt-4">
        <button onClick={downloadCSV} className="px-4 py-1.5 rounded-full text-sm font-medium bg-slate-100 text-aic-dark hover:bg-slate-200 transition">
          Download CSV
        </button>
        <button onClick={downloadPNG} className="px-4 py-1.5 rounded-full text-sm font-medium bg-slate-100 text-aic-dark hover:bg-slate-200 transition">
          Download Chart (PNG)
        </button>
      </div>
    </div>
  );
}
