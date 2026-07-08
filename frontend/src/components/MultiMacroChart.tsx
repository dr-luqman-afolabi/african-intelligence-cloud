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
  Brush,
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

type ViewMode = "line" | "bar" | "table";

const compactFmt = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 });
const fullFmt = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

function fmt(v: number | null | undefined, compact = true): string {
  if (v == null || Number.isNaN(v)) return "—";
  return (compact && Math.abs(v) >= 10000 ? compactFmt : fullFmt).format(v);
}

interface SeriesStats {
  latest: number;
  latestYear: number;
  changePct: number | null;
  cagrPct: number | null;
  peak: number;
  peakYear: number;
}

function computeStats(data: { year: number; value: number }[]): SeriesStats | null {
  const pts = data.filter((d) => d.value != null && !Number.isNaN(d.value));
  if (pts.length === 0) return null;
  const first = pts[0];
  const last = pts[pts.length - 1];
  let peak = pts[0];
  for (const p of pts) if (p.value > peak.value) peak = p;
  const years = last.year - first.year;
  const changePct = first.value !== 0 ? ((last.value - first.value) / Math.abs(first.value)) * 100 : null;
  const cagrPct =
    years > 0 && first.value > 0 && last.value > 0
      ? (Math.pow(last.value / first.value, 1 / years) - 1) * 100
      : null;
  return { latest: last.value, latestYear: last.year, changePct, cagrPct, peak: peak.value, peakYear: peak.year };
}

export default function MultiMacroChart({ series }: MultiMacroChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("line");
  const [normalize, setNormalize] = useState(false);
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  const merged = useMemo(() => {
    const years = new Set<number>();
    series.forEach((s) => s.data.forEach((d) => years.add(d.year)));
    const sortedYears = Array.from(years).sort((a, b) => a - b);

    // Base value per series for index mode: its first non-null observation.
    const base: Record<string, number> = {};
    series.forEach((s) => {
      const firstPoint = s.data.find((d) => d.value != null && d.value !== 0);
      if (firstPoint) base[s.code] = firstPoint.value;
    });

    return sortedYears.map((year) => {
      const row: Record<string, number | null> = { year };
      series.forEach((s) => {
        const point = s.data.find((d) => d.year === year);
        const raw = point ? point.value : null;
        row[s.code] =
          normalize && raw != null && base[s.code] ? (raw / base[s.code]) * 100 : raw;
      });
      return row;
    });
  }, [series, normalize]);

  const stats = useMemo(
    () => series.map((s) => ({ series: s, stats: computeStats(s.data) })),
    [series]
  );

  function toggleSeries(code: string) {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  }

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

  const legendPayload = series.map((s, i) => ({
    value: s.label,
    id: s.code,
    dataKey: s.code,
    type: "line" as const,
    color: hidden.has(s.code) ? "#cbd5e1" : s.color || COLORS[i % COLORS.length],
  }));

  const axisProps = {
    tick: { fontSize: 12, fill: "#64748b" },
    tickLine: false,
  };

  const commonChildren = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
      <XAxis dataKey="year" {...axisProps} />
      <YAxis {...axisProps} tickFormatter={(v: number) => fmt(v)} width={70} />
      <Tooltip
        formatter={(value: number, name: string) => [
          normalize ? `${fullFmt.format(value)} (index)` : fmt(value, false),
          name,
        ]}
        labelFormatter={(year) => `Year: ${year}`}
      />
      <Legend
        payload={legendPayload}
        onClick={(entry) => {
          const key = (entry as { dataKey?: unknown }).dataKey;
          if (typeof key === "string") toggleSeries(key);
        }}
        wrapperStyle={{ cursor: "pointer", userSelect: "none" }}
      />
      <Brush dataKey="year" height={22} stroke="#0f766e" travellerWidth={8} fill="#f8fafc" />
    </>
  );

  return (
    <div>
      {/* Per-indicator stat cards: the numbers behind the lines */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {stats.map(({ series: s, stats: st }, i) =>
          st ? (
            <button
              key={s.code}
              type="button"
              onClick={() => toggleSeries(s.code)}
              title="Click to show/hide this series on the chart"
              className={
                "text-left rounded-xl border p-3 transition " +
                (hidden.has(s.code)
                  ? "border-slate-100 bg-slate-50 opacity-50"
                  : "border-slate-200 bg-white hover:border-slate-300")
              }
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: s.color || COLORS[i % COLORS.length] }}
                />
                <p className="text-xs text-aic-muted truncate">{s.label}</p>
              </div>
              <p className="text-lg font-bold text-aic-dark leading-tight">
                {fmt(st.latest)} <span className="text-xs font-normal text-aic-muted">({st.latestYear})</span>
              </p>
              <p className="text-xs text-aic-muted mt-0.5">
                {st.changePct != null && (
                  <span className={st.changePct >= 0 ? "text-green-700" : "text-red-700"}>
                    {st.changePct >= 0 ? "▲" : "▼"} {Math.abs(st.changePct).toFixed(1)}%
                  </span>
                )}
                {st.cagrPct != null && <span> · {st.cagrPct.toFixed(1)}%/yr</span>}
                <span> · peak {fmt(st.peak)} ({st.peakYear})</span>
              </p>
            </button>
          ) : null
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <label className="flex items-center gap-2 text-xs font-medium text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={normalize}
            onChange={(e) => setNormalize(e.target.checked)}
            className="accent-aic-dark"
          />
          Index mode (first year = 100) — compare indicators with different units
        </label>
        <div className="inline-flex rounded-full bg-slate-100 p-1">
          {(["line", "bar", "table"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={
                viewMode === mode
                  ? "px-3 py-1 rounded-full text-xs font-medium bg-aic-dark text-white transition capitalize"
                  : "px-3 py-1 rounded-full text-xs font-medium text-slate-600 hover:text-aic-dark transition capitalize"
              }
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {viewMode === "table" ? (
        <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-200 rounded-xl">
          <table className="w-full text-sm text-left">
            <thead className="sticky top-0 bg-slate-50">
              <tr className="text-aic-muted border-b border-slate-200">
                <th className="py-2 px-3">Year</th>
                {series.map((s) => (
                  <th key={s.code} className="py-2 px-3">{s.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...merged].reverse().map((row) => (
                <tr key={String(row.year)} className="border-b border-slate-100">
                  <td className="py-1.5 px-3 font-medium">{row.year}</td>
                  {series.map((s) => (
                    <td key={s.code} className="py-1.5 px-3">{fmt(row[s.code] as number | null, false)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div ref={containerRef}>
          <ResponsiveContainer width="100%" height={400}>
            {viewMode === "line" ? (
              <LineChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }} data={merged}>
                {commonChildren}
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
                    hide={hidden.has(s.code)}
                  />
                ))}
              </LineChart>
            ) : (
              <BarChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }} data={merged}>
                {commonChildren}
                {series.map((s, i) => (
                  <Bar
                    key={s.code}
                    dataKey={s.code}
                    name={s.label}
                    fill={s.color || COLORS[i % COLORS.length]}
                    hide={hidden.has(s.code)}
                  />
                ))}
              </BarChart>
            )}
          </ResponsiveContainer>
          <p className="text-xs text-aic-muted mt-1">
            Drag the slider below the chart to zoom a year range · click a legend item or stat card to show/hide a series
          </p>
        </div>
      )}

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
