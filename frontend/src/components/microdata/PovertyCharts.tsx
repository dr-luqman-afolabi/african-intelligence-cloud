"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/** One row of the backend's group-by poverty table (tables[groupVar]). */
export interface GroupPovertyRow {
  group: string;
  headcount: number;
  poverty_gap: number;
  squared_poverty_gap: number;
  gini?: number | null;
  n_obs?: number | null;
}

const COLORS = ["#006B3C", "#FFC20E", "#CE1126", "#0F172A", "#64748B", "#0a7a4d"];
const PCT = (v: number) => `${(v * 100).toFixed(1)}%`;

export function GroupBarChart({
  data,
  dataKey,
  label,
  chartType = "bar",
}: {
  data: GroupPovertyRow[];
  dataKey: "headcount" | "poverty_gap" | "squared_poverty_gap";
  label: string;
  chartType?: "bar" | "line" | "pie";
}) {
  if (data.length === 0) {
    return <div className="text-center text-sm text-slate-400 py-12">No group breakdown available.</div>;
  }

  if (chartType === "pie") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie data={data} dataKey={dataKey} nameKey="group" outerRadius={110} label={(d) => `${d.group}: ${PCT(d[dataKey])}`}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => [PCT(v), label]} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="group" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={PCT} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v: number) => [PCT(v), label]} />
          <Line type="monotone" dataKey={dataKey} stroke="#006B3C" strokeWidth={2.5} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="group" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={PCT} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => [PCT(v), label]} />
        <Bar dataKey={dataKey} fill="#006B3C" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function GroupRankingTable({ data }: { data: GroupPovertyRow[] }) {
  if (data.length === 0) {
    return <div className="text-center text-sm text-slate-400 py-12">No ranking data available.</div>;
  }
  const fmt = (v: number | null | undefined, digits = 3) =>
    typeof v === "number" ? v.toFixed(digits) : "—";
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200">
            <th className="py-2 pr-4">#</th>
            <th className="py-2 pr-4">Group</th>
            <th className="py-2 pr-4">Headcount</th>
            <th className="py-2 pr-4">Gap</th>
            <th className="py-2 pr-4">Severity</th>
            <th className="py-2 pr-4">Gini</th>
            <th className="py-2 pr-4">Sample (n)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((g, i) => (
            <tr key={g.group} className="border-b border-slate-100">
              <td className="py-2 pr-4 text-slate-400">{i + 1}</td>
              <td className="py-2 pr-4 font-medium text-slate-800">{g.group}</td>
              <td className="py-2 pr-4">{PCT(g.headcount)}</td>
              <td className="py-2 pr-4">{PCT(g.poverty_gap)}</td>
              <td className="py-2 pr-4">{PCT(g.squared_poverty_gap)}</td>
              <td className="py-2 pr-4">{fmt(g.gini)}</td>
              <td className="py-2 pr-4 text-slate-500">{g.n_obs ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
