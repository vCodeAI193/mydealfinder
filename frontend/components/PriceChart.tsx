"use client";

import { useMemo } from "react";
import type { PricePoint } from "@/lib/api";

// A dependency-free SVG line chart of the best (minimum) price per day.
export default function PriceChart({ points }: { points: PricePoint[] }) {
  const series = useMemo(() => buildDailyBest(points), [points]);

  if (series.length < 2) {
    return <div className="muted">Not enough history to plot yet.</div>;
  }

  const width = 720;
  const height = 220;
  const pad = { top: 16, right: 16, bottom: 28, left: 48 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const prices = series.map((d) => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const span = max - min || 1;

  const x = (i: number) => pad.left + (i / (series.length - 1)) * innerW;
  const y = (price: number) =>
    pad.top + innerH - ((price - min) / span) * innerH;

  const path = series
    .map((d, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(d.price).toFixed(1)}`)
    .join(" ");

  const areaPath = `${path} L ${x(series.length - 1).toFixed(1)} ${pad.top + innerH} L ${x(0).toFixed(1)} ${pad.top + innerH} Z`;

  const ticks = [min, min + span / 2, max];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      role="img"
      aria-label="Price history chart"
    >
      {ticks.map((t, i) => (
        <g key={i}>
          <line
            x1={pad.left}
            x2={width - pad.right}
            y1={y(t)}
            y2={y(t)}
            stroke="#2c313c"
            strokeWidth={1}
          />
          <text x={8} y={y(t) + 4} fill="#9aa3b2" fontSize={11}>
            ${t.toFixed(0)}
          </text>
        </g>
      ))}

      <path d={areaPath} fill="rgba(47,191,113,0.12)" stroke="none" />
      <path d={path} fill="none" stroke="#2fbf71" strokeWidth={2} />

      <text x={pad.left} y={height - 6} fill="#9aa3b2" fontSize={11}>
        {series[0].date}
      </text>
      <text
        x={width - pad.right}
        y={height - 6}
        fill="#9aa3b2"
        fontSize={11}
        textAnchor="end"
      >
        {series[series.length - 1].date}
      </text>
    </svg>
  );
}

// Collapse all source price points into one "best price per day" series.
function buildDailyBest(points: PricePoint[]): { date: string; price: number }[] {
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
