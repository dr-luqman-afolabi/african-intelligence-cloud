"use client";

import { useMemo } from "react";
import { MapContainer, TileLayer, GeoJSON, Tooltip } from "react-leaflet";
import type { Feature } from "geojson";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export interface ChoroplethMapProps {
  geojson: GeoJSON.FeatureCollection;
  valueField: string; // e.g. "poverty_headcount", "crop_yield", "crop_simpson_index"
  label: string; // legend title, e.g. "Poverty headcount"
  formatValue?: (v: number) => string;
}

// Sequential green-to-red ramp: low values render green, high values red —
// appropriate for "bad when high" metrics like poverty. Callers mapping
// "good when high" metrics (e.g. crop yield) can pass reverse via CSS order
// of thresholds since the ramp is computed from data quantiles either way.
const COLORS = ["#1a9850", "#91cf60", "#d9ef8b", "#fee08b", "#fc8d59", "#d73027"];

function quantileBreaks(values: number[], classes: number): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  const breaks: number[] = [];
  for (let i = 1; i < classes; i++) {
    const idx = Math.floor((i / classes) * (sorted.length - 1));
    breaks.push(sorted[idx]);
  }
  return breaks;
}

export default function ChoroplethMap({ geojson, valueField, label, formatValue }: ChoroplethMapProps) {
  const fmt = formatValue ?? ((v: number) => v.toFixed(2));

  const { breaks, bounds } = useMemo(() => {
    const values = geojson.features
      .map((f) => f.properties?.[valueField])
      .filter((v): v is number => typeof v === "number");
    const layer = L.geoJSON(geojson as GeoJSON.GeoJsonObject);
    return {
      breaks: values.length >= 2 ? quantileBreaks(values, COLORS.length) : [],
      bounds: layer.getBounds(),
    };
  }, [geojson, valueField]);

  function colorFor(value: number | undefined | null): string {
    if (typeof value !== "number") return "#cbd5e1";
    for (let i = 0; i < breaks.length; i++) {
      if (value <= breaks[i]) return COLORS[i];
    }
    return COLORS[COLORS.length - 1];
  }

  function style(feature?: Feature) {
    return {
      fillColor: colorFor(feature?.properties?.[valueField]),
      weight: 1,
      color: "#475569",
      fillOpacity: 0.75,
    };
  }

  function downloadGeoJSON() {
    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "aic-spatial-analysis.geojson";
    link.click();
    URL.revokeObjectURL(url);
  }

  if (!geojson.features?.length) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center h-64 text-aic-muted text-sm text-center px-6">
        No boundary features matched the analysis results. Upload boundaries via the Spatial
        Boundaries endpoint or supply a GeoJSON file whose admin names match your geography variable.
      </div>
    );
  }

  return (
    <div>
      <div className="rounded-xl overflow-hidden border border-slate-200" style={{ height: 420 }}>
        <MapContainer bounds={bounds} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {geojson.features.map((feature, idx) => {
            const props = feature.properties ?? {};
            const name = props.admin_name || props.geo_value || `Unit ${idx + 1}`;
            const value = props[valueField];
            return (
              <GeoJSON key={`${name}-${idx}`} data={feature as GeoJSON.GeoJsonObject} style={() => style(feature as Feature)}>
                <Tooltip sticky>
                  <div className="text-xs">
                    <strong>{name}</strong>
                    <br />
                    {label}: {typeof value === "number" ? fmt(value) : "—"}
                    {typeof props.rank === "number" && (
                      <>
                        <br />
                        Rank: {props.rank}
                      </>
                    )}
                  </div>
                </Tooltip>
              </GeoJSON>
            );
          })}
        </MapContainer>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mt-3">
        <div className="flex items-center gap-1 text-xs text-aic-muted">
          <span className="mr-1 font-medium text-aic-dark">{label}:</span>
          <span>low</span>
          {COLORS.map((c) => (
            <span key={c} className="inline-block w-6 h-3 rounded-sm" style={{ backgroundColor: c }} />
          ))}
          <span>high</span>
        </div>
        <button
          onClick={downloadGeoJSON}
          className="px-4 py-1.5 rounded-full text-sm font-medium bg-slate-100 text-aic-dark hover:bg-slate-200 transition"
        >
          Download GeoJSON
        </button>
      </div>
    </div>
  );
}
