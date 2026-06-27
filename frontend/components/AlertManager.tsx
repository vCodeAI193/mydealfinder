"use client";

import { useEffect, useState } from "react";
import { api, formatPrice, type Alert } from "@/lib/api";
import { getStoredUser, onAuthChange } from "@/lib/auth";

// Look up alerts by email and pause/resume them (F032). Signed-in users get
// their alerts loaded automatically (F035 coupling).
export default function AlertManager() {
  const [email, setEmail] = useState("");
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sync = () => {
      const user = getStoredUser();
      if (user) {
        setEmail(user.email);
        api.myAlerts().then(setAlerts).catch(() => {});
      }
    };
    sync();
    return onAuthChange(sync);
  }, []);

  async function load(addr: string) {
    if (!addr.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setAlerts(await api.listAlerts(addr.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load alerts");
    } finally {
      setLoading(false);
    }
  }

  async function toggle(a: Alert) {
    const updated = a.status === "paused" ? await api.resumeAlert(a.id) : await api.pauseAlert(a.id);
    setAlerts((prev) => prev?.map((x) => (x.id === updated.id ? updated : x)) ?? null);
  }

  function describe(a: Alert): string {
    if (a.alert_type === "restock") return "back in stock";
    if (a.alert_type === "percentage") {
      return `${a.threshold_pct}% drop (≤ ${formatPrice(a.effective_threshold, a.currency)})`;
    }
    return `below ${formatPrice(a.threshold_price, a.currency)}`;
  }

  return (
    <div>
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          load(email);
        }}
      >
        <div className="field" style={{ flex: 2, minWidth: 220 }}>
          <label htmlFor="manage-email">Manage your alerts</label>
          <input
            id="manage-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <button type="submit" className="secondary" disabled={loading}>
          {loading ? "Loading…" : "Load alerts"}
        </button>
      </form>

      {error && <div className="notice err">{error}</div>}

      {alerts && alerts.length === 0 && <p className="muted">No alerts for this email yet.</p>}

      {alerts && alerts.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Target</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>#{a.product_id}</td>
                <td className="muted">
                  {describe(a)}
                  {a.recurring && <span className="badge" style={{ marginLeft: 6 }}>recurring</span>}
                  {a.frequency !== "instant" && (
                    <span className="badge" style={{ marginLeft: 6 }}>{a.frequency}</span>
                  )}
                  {a.channel === "webhook" && (
                    <span className="badge" style={{ marginLeft: 6 }}>webhook</span>
                  )}
                </td>
                <td>
                  <span className="badge">{a.status}</span>
                </td>
                <td>
                  {a.status !== "triggered" && (
                    <button
                      type="button"
                      className="secondary"
                      style={{ padding: "4px 10px", fontSize: 13 }}
                      onClick={() => toggle(a)}
                    >
                      {a.status === "paused" ? "Resume" : "Pause"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
