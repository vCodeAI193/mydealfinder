"use client";

import { useEffect, useState } from "react";
import { api, type AlertChannel, type AlertFrequency, type AlertType } from "@/lib/api";
import { getStoredUser, onAuthChange } from "@/lib/auth";

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
  const [channel, setChannel] = useState<AlertChannel>("email");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [frequency, setFrequency] = useState<AlertFrequency>("instant");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Prefill the email from the signed-in account (F035 coupling).
  useEffect(() => {
    const sync = () => {
      const user = getStoredUser();
      if (user) setEmail((e) => e || user.email);
    };
    sync();
    return onAuthChange(sync);
  }, []);

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
        channel,
        webhook_url: channel === "webhook" ? webhookUrl : undefined,
        frequency,
      });
      const target =
        type === "restock"
          ? "it is back in stock"
          : type === "absolute"
          ? `the price drops below ${threshold} ${currency}`
          : `the price drops ${pct}%`;
      setStatus({ ok: true, msg: `Alert set! We'll notify ${email} when ${target}.` });
    } catch (err) {
      setStatus({ ok: false, msg: err instanceof Error ? err.message : "Could not create alert." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="row" onSubmit={submit}>
      <div className="field" style={{ flex: 2, minWidth: 200 }}>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>

      <div className="field" style={{ minWidth: 130 }}>
        <label htmlFor="type">Alert type</label>
        <select id="type" value={type} onChange={(e) => setType(e.target.value as AlertType)}>
          <option value="absolute">Below price</option>
          <option value="percentage">% drop</option>
          <option value="restock">Back in stock</option>
        </select>
      </div>

      {type === "absolute" && (
        <div className="field" style={{ minWidth: 140 }}>
          <label htmlFor="threshold">Notify below ({currency})</label>
          <input id="threshold" type="number" min="0" step="0.01" required value={threshold} onChange={(e) => setThreshold(e.target.value)} />
        </div>
      )}
      {type === "percentage" && (
        <div className="field" style={{ minWidth: 110 }}>
          <label htmlFor="pct">Drop by (%)</label>
          <input id="pct" type="number" min="1" max="100" step="1" required value={pct} onChange={(e) => setPct(e.target.value)} />
        </div>
      )}

      <div className="field" style={{ minWidth: 120 }}>
        <label htmlFor="freq">Frequency</label>
        <select id="freq" value={frequency} onChange={(e) => setFrequency(e.target.value as AlertFrequency)}>
          <option value="instant">Instant</option>
          <option value="daily">Daily digest</option>
          <option value="weekly">Weekly digest</option>
        </select>
      </div>

      <div className="field" style={{ minWidth: 120 }}>
        <label htmlFor="channel">Channel</label>
        <select id="channel" value={channel} onChange={(e) => setChannel(e.target.value as AlertChannel)}>
          <option value="email">Email</option>
          <option value="webhook">Webhook</option>
        </select>
      </div>
      {channel === "webhook" && (
        <div className="field" style={{ flex: 2, minWidth: 220 }}>
          <label htmlFor="hook">Webhook URL</label>
          <input id="hook" type="url" required placeholder="https://hooks.example.com/…" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
        </div>
      )}

      <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
        <input type="checkbox" checked={recurring} onChange={(e) => setRecurring(e.target.checked)} style={{ width: "auto" }} />
        <span className="muted">Recurring</span>
      </label>

      {type !== "restock" && (
        <button type="button" className="secondary" onClick={suggest} title="Suggest a target from price history">
          Suggest
        </button>
      )}
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
