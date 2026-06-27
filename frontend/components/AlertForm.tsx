"use client";

import { useState } from "react";
import { api } from "@/lib/api";

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
  const [threshold, setThreshold] = useState(
    suggested ? Math.floor(suggested * 0.9).toString() : ""
  );
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      await api.createAlert({
        product_id: productId,
        email,
        threshold_price: Number(threshold),
        currency,
      });
      setStatus({
        ok: true,
        msg: `Alert set! We'll notify ${email} when the price drops below ${threshold} ${currency}.`,
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
