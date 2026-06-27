"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type AlertType = "absolute" | "percentage";

export default function AlertForm({
  productId,
  currency,
  suggested,
}: {
  productId: number;
  currency: string;
  suggested: number | null;
}) {
  const [email, setEmail] = useState("");
  const [type, setType] = useState<AlertType>("absolute");
  const [threshold, setThreshold] = useState(
    suggested ? Math.floor(suggested * 0.9).toString() : ""
  );
  const [pct, setPct] = useState("10");
  const [recurring, setRecurring] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function suggest() {
    setStatus(null);
    try {
      const s = await api.alertSuggestion(productId);
      if (s.suggested_threshold != null) {
        setType("absolute");
        setThreshold(String(s.suggested_threshold));
        setStatus({
          ok: true,
          msg: `Suggested ${s.suggested_threshold} ${currency} (avg ${s.avg_price}, now ${s.current_price}).`,
        });
      }
    } catch (err) {
      setStatus({ ok: false, msg: err instanceof Error ? err.message : "Could not suggest." });
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      await api.createAlert({
        product_id: productId,
        email,
        alert_type: type,
        threshold_price: type === "absolute" ? Number(threshold) : undefined,
        threshold_pct: type === "percentage" ? Number(pct) : undefined,
        recurring,
        currency,
      });
      const target =
        type === "absolute" ? `${threshold} ${currency}` : `${pct}% below the current price`;
      setStatus({
        ok: true,
        msg: `Alert set! We'll notify ${email} when the price drops below ${target}.`,
      });
      setEmail("");
    } catch (err) {
      setStatus({
        ok: false,
        msg: err instanceof Error ? err.message : "Could not create alert.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="row" onSubmit={submit}>
      <div className="field" style={{ flex: 2, minWidth: 220 }}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div className="field" style={{ minWidth: 130 }}>
        <label htmlFor="type">Alert type</label>
        <select id="type" value={type} onChange={(e) => setType(e.target.value as AlertType)}>
          <option value="absolute">Below price</option>
          <option value="percentage">% drop</option>
        </select>
      </div>

      {type === "absolute" ? (
        <div className="field" style={{ flex: 1, minWidth: 140 }}>
          <label htmlFor="threshold">Notify below ({currency})</label>
          <input
            id="threshold"
            type="number"
            min="0"
            step="0.01"
            required
            placeholder="e.g. 199.99"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
          />
        </div>
      ) : (
        <div className="field" style={{ minWidth: 120 }}>
          <label htmlFor="pct">Drop by (%)</label>
          <input
            id="pct"
            type="number"
            min="1"
            max="100"
            step="1"
            required
            value={pct}
            onChange={(e) => setPct(e.target.value)}
          />
        </div>
      )}

      <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
        <input
          type="checkbox"
          checked={recurring}
          onChange={(e) => setRecurring(e.target.checked)}
          style={{ width: "auto" }}
        />
        <span className="muted">Recurring</span>
      </label>

      <button type="button" className="secondary" onClick={suggest} title="Suggest a target from price history">
        Suggest
      </button>
      <button type="submit" disabled={submitting}>
        {submitting ? "Saving…" : "Set price alert"}
      </button>

      {status && (
        <div className={`notice ${status.ok ? "ok" : "err"}`} style={{ width: "100%" }}>
          {status.msg}
        </div>
      )}
    </form>
  );
}
