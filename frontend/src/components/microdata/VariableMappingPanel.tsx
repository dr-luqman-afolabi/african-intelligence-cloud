"use client";

import { useEffect, useState } from "react";
import {
  fetchVariableMapping,
  saveVariableMapping,
  suggestVariableMapping,
  type MicrodataVariable,
  type VariableMappingEntry,
} from "@/lib/api";

// Concepts shown in the panel, grouped for readability. Matches the backend
// StandardConcept enum values.
const CONCEPT_GROUPS: { title: string; concepts: string[] }[] = [
  { title: "Identifiers & design", concepts: ["household_id", "weight", "strata", "cluster"] },
  { title: "Geography", concepts: ["country", "region", "province", "district", "sector", "urban_rural"] },
  { title: "Demographics", concepts: ["gender", "age", "education", "household_size"] },
  { title: "Welfare", concepts: ["welfare", "consumption", "income", "poverty_status"] },
  {
    title: "Agriculture",
    concepts: ["land_area", "crop_output", "crop_value", "livestock", "fertilizer", "improved_seed", "irrigation", "extension"],
  },
];

interface Props {
  datasetId: string;
  variables: MicrodataVariable[];
  onSaved?: (mapping: Record<string, string>) => void;
  // Fired after the initial fetch when the dataset already has a saved
  // mapping, so parents can enable mapping-dependent actions immediately.
  onLoadedExisting?: (mapping: Record<string, string>) => void;
}

export default function VariableMappingPanel({ datasetId, variables, onSaved, onLoadedExisting }: Props) {
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [confidences, setConfidences] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autoMapping, setAutoMapping] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setMessage(null);
    fetchVariableMapping(datasetId)
      .then((rows) => {
        const m: Record<string, string> = {};
        rows.forEach((r) => {
          m[r.standard_concept] = r.raw_variable_name;
        });
        setMapping(m);
        setConfidences({});
        if (rows.length > 0) onLoadedExisting?.(m);
      })
      .catch(() => setMapping({}))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  async function handleAutoMap() {
    setAutoMapping(true);
    setMessage(null);
    try {
      const res = await suggestVariableMapping(datasetId);
      const m: Record<string, string> = { ...mapping };
      const conf: Record<string, number> = {};
      res.suggestions.forEach((s: VariableMappingEntry) => {
        // Auto-detection never overwrites a concept the user already set.
        if (!mapping[s.standard_concept]) {
          m[s.standard_concept] = s.raw_variable_name;
          if (s.confidence != null) conf[s.standard_concept] = s.confidence;
        }
      });
      setMapping(m);
      setConfidences(conf);
      setMessage(`Auto-detected ${res.suggestions.length} candidate mapping(s). Review and save.`);
    } catch {
      setMessage("Auto-detection failed. You can still map variables manually.");
    } finally {
      setAutoMapping(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    try {
      const entries: VariableMappingEntry[] = Object.entries(mapping)
        .filter(([, raw]) => raw)
        .map(([concept, raw]) => ({
          standard_concept: concept,
          raw_variable_name: raw,
          confidence: confidences[concept] ?? null,
        }));
      await saveVariableMapping(datasetId, entries);
      setMessage(`Saved ${entries.length} mapping(s).`);
      onSaved?.(mapping);
    } catch {
      setMessage("Could not save the mapping. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  function setConcept(concept: string, raw: string) {
    setMapping((prev) => {
      const next = { ...prev };
      if (raw) next[concept] = raw;
      else delete next[concept];
      return next;
    });
    setConfidences((prev) => {
      const next = { ...prev };
      delete next[concept]; // manual choice — drop the auto-detect confidence
      return next;
    });
  }

  if (loading) return <p className="text-aic-muted text-sm">Loading variable mapping...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <button
          type="button"
          onClick={handleAutoMap}
          disabled={autoMapping}
          className="bg-aic-dark text-white px-4 py-1.5 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {autoMapping ? "Detecting..." : "Auto map variables"}
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || Object.keys(mapping).length === 0}
          className="bg-aic-green text-white px-4 py-1.5 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save mapping"}
        </button>
        {message && <p className="text-sm text-aic-muted">{message}</p>}
      </div>

      <div className="space-y-5">
        {CONCEPT_GROUPS.map((group) => (
          <div key={group.title}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">{group.title}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {group.concepts.map((concept) => (
                <div key={concept}>
                  <label className="block text-xs font-medium text-aic-dark mb-1">
                    {concept.replace(/_/g, " ")}
                    {confidences[concept] != null && (
                      <span className="ml-1 text-aic-muted font-normal">({confidences[concept]}%)</span>
                    )}
                  </label>
                  <select
                    value={mapping[concept] ?? ""}
                    onChange={(e) => setConcept(concept, e.target.value)}
                    className="border border-slate-300 rounded-lg px-2 py-1.5 w-full text-sm"
                  >
                    <option value="">—</option>
                    {variables.map((v) => (
                      <option key={v.id} value={v.variable_name}>
                        {v.variable_name}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
