"use client";

import type { MicrodataVariable } from "@/lib/api";

interface Props {
  label: string;
  variables: MicrodataVariable[];
  value: string;
  onChange: (value: string) => void;
  allowNone?: boolean;
  disabled?: boolean;
}

export default function VariableSelect({ label, variables, value, onChange, allowNone, disabled }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || variables.length === 0}
        className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-aic-green disabled:bg-slate-50 disabled:text-slate-400 w-full"
      >
        {allowNone && <option value="">None</option>}
        {!allowNone && <option value="">Select…</option>}
        {variables.map((v) => (
          <option key={v.id} value={v.variable_name}>
            {v.variable_name}{v.inferred_dtype ? ` (${v.inferred_dtype})` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
