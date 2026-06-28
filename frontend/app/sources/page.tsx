"use client";

import { useEffect, useState } from "react";
import { api, type SourcesHealth } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  ok: "var(--accent-2)",
  error: "var(--danger)",
  unknown: "var(--muted)",
};

// Read-only data-source health dashboard (F049).
export default function SourcesPage() {
  const [data, setData] = useState<SourcesHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    api
      .sourcesHealth()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));

  useEffect(() => {
    load();
  }, []);

  return (
    <main>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>Data sources</h1>
        <button type="button" className="secondary" onClick={load} style={{ padding: "6px 12px", fontSize: 13 }}>
          ↻ Reload
        </button>
      </div>

      {error && <div className="notice err">{error}</div>}

      {data && (
        <>
          <p className="muted">
            Rate limit:{" "}
            {data.rate_limit_per_minute > 0 ? `${data.rate_limit_per_minute}/min per source` : "unlimited"}
          </p>
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Status</th>
                <th>OK</th>
                <th>Errors</th>
                <th>Last error</th>
              </tr>
            </thead>
            <tbody>
              {data.sources.map((s) => (
                <tr key={s.source}>
                  <td style={{ textTransform: "capitalize" }}>{s.source}</td>
                  <td>
                    <span className="badge" style={{ color: STATUS_COLOR[s.status] }}>
                      ● {s.status}
                    </span>
                  </td>
                  <td className="muted">{s.ok_count}</td>
                  <td className="muted">{s.error_count}</td>
                  <td className="muted" style={{ fontSize: 12 }}>
                    {s.last_error_message || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
