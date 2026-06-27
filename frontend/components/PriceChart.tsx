"use client";

import { useMemo } from "react";
import type { PricePoint } from "@/lib/api";

type Mode = "best" | "source";

const SOURCE_COLORS = ["#4f9dff", "#2fbf71", "#ff9f43", "#c678dd", "#ff6b6b"];

// A dependency-free SVG line chart with optional per-source series (F018)
// and min/max/avg reference markers (F019).
export default function PriceChart({
  points,
  mode = "best",
}: {
  points: PricePoint[];
  mode?: Mode;
}) {
  const series = useMemo(() => buildSeries(points, mode), [points, mode]);
  const stats = useMemo(() => buildStats(points), [points]);

  const allValues = series.flatMap((s) => s.data.map((d) => d.price));
  if (allValues.length < 2) {
    return <div className="muted">Not enough history to plot yet.</div>;
  }

  const width = 720;
  const height = 240;
  const pad = { top: 16, right: 16, bottom: 28, left: 48 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const span = max - min || 1;
  const maxLen = Math.max(...series.map((s) => s.data.length));

  const x = (i: number) => pad.left + (i / Math.max(maxLen - 1, 1)) * innerW;
  const y = (price: number) => pad.top + innerH - ((price - min) / span) * innerH;

  const ticks = [min, min + span / 2, max];
  const firstSeries = series[0].data;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label="Price history chart">
        {ticks.map((t, i) => (
          <g key={`t${i}`}>
            <line x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)} stroke="#2c313c" strokeWidth={1} />
            <text x={8} y={y(t) + 4} fill="#9aa3b2" fontSize={11}>${t.toFixed(0)}</text>
          </g>
        ))}

        {/* Min / max / average reference markers (F019), best-mode only. */}
        {mode === "best" && stats && (
          <>
            {[
              { label: "max", value: stats.max, color: "#ff6b6b" },
              { label: "avg", value: stats.avg, color: "#9aa3b2" },
              { label: "min", value: stats.min, color: "#2fbf71" },
            ].map((m) => (
              <g key={m.label}>
                <line
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={y(m.value)}
                  y2={y(m.value)}
                  stroke={m.color}
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  opacity={0.7}
                />
                <text x={width - pad.right} y={y(m.value) - 4} fill={m.color} fontSize={10} textAnchor="end">
                  {m.label} ${m.value.toFixed(0)}
                </text>
              </g>
            ))}
          </>
        )}

        {series.map((s, si) => {
          const path = s.data
            .map((d, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(d.price).toFixed(1)}`)
            .join(" ");
          return <path key={s.name} d={path} fill="none" stroke={s.color} strokeWidth={2} />;
        })}

        <text x={pad.left} y={height - 6} fill="#9aa3b2" fontSize={11}>
          {firstSeries[0]?.date}
        </text>
        <text x={width - pad.right} y={height - 6} fill="#9aa3b2" fontSize={11} textAnchor="end">
          {firstSeries[firstSeries.length - 1]?.date}
        </text>
      </svg>

      {mode === "source" && (
        <div className="row" style={{ gap: 16, marginTop: 8 }}>
          {series.map((s) => (
            <span key={s.name} className="muted" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 12, height: 3, background: s.color, display: "inline-block" }} />
              {s.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

interface Series {
  name: string;
  color: string;
  data: { date: string; price: number }[];
}

function buildSeries(points: PricePoint[], mode: Mode): Series[] {
  if (mode === "source") {
    const bySource = new Map<string, PricePoint[]>();
    for (const p of points) {
      const list = bySource.get(p.source) || [];
      list.push(p);
      bySource.set(p.source, list);
    }
    return Array.from(bySource.entries()).map(([name, pts], i) => ({
      name,
      color: SOURCE_COLORS[i % SOURCE_COLORS.length],
      data: dailyBest(pts),
    }));
  }
  return [{ name: "best", color: "#2fbf71", data: dailyBest(points) }];
}

// Collapse points into one "best price per day" series.
function dailyBest(points: PricePoint[]): { date: string; price: number }[] {
  const byDay = new Map<string, number>();
  for (const p of points) {
    const day = p.recorded_at.slice(0, 10);
    const cur = byDay.get(day);
    if (cur === undefined || p.price < cur) byDay.set(day, p.price);
  }
  return Array.from(byDay.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, price]) => ({ date, price }));
}

function buildStats(points: PricePoint[]): { min: number; max: number; avg: number } | null {
  const daily = dailyBest(points).map((d) => d.price);
  if (!daily.length) return null;
  return {
    min: Math.min(...daily),
    max: Math.max(...daily),
    avg: daily.reduce((a, b) => a + b, 0) / daily.length,
  };
}
