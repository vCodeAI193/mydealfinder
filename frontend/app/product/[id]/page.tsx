"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  formatPrice,
  type PriceAnalytics,
  type PriceHistory,
  type ProductDetail,
} from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import AlertForm from "@/components/AlertForm";
import AlertManager from "@/components/AlertManager";

// History windows offered in the UI (F017). null = all history.
const RANGES: { label: string; days: number | null }[] = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
  { label: "All", days: null },
];

export default function ProductPage({ params }: { params: { id: string } }) {
  const productId = Number(params.id);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [history, setHistory] = useState<PriceHistory | null>(null);
  const [analytics, setAnalytics] = useState<PriceAnalytics | null>(null);
  const [days, setDays] = useState<number | null>(30);
  const [chartMode, setChartMode] = useState<"best" | "source">("best");
  const [error, setError] = useState<string | null>(null);

  // Load the product once.
  useEffect(() => {
    let active = true;
    api
      .product(productId)
      .then((p) => active && setProduct(p))
      .catch((e) => active && setError(e instanceof Error ? e.message : "Failed to load product"));
    return () => {
      active = false;
    };
  }, [productId]);

  // Reload history + analytics whenever the selected range changes (F017).
  useEffect(() => {
    let active = true;
    Promise.all([api.history(productId, days), api.analytics(productId, days)])
      .then(([h, a]) => {
        if (!active) return;
        setHistory(h);
        setAnalytics(a);
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : "Failed to load history"));
    return () => {
      active = false;
    };
  }, [productId, days]);

  if (error) {
    return (
      <main>
        <div className="notice err">{error}</div>
        <p>
          <Link href="/">← Back to search</Link>
        </p>
      </main>
    );
  }

  if (!product) {
    return <main className="empty">Loading…</main>;
  }

  const best = product.offers[0];

  return (
    <main>
      <p>
        <Link href="/">← Back to search</Link>
      </p>

      <div className="row" style={{ alignItems: "flex-start", gap: 24 }}>
        {product.image_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name}
            width={200}
            height={200}
            style={{ borderRadius: 12, objectFit: "cover", background: "var(--surface-2)" }}
          />
        )}
        <div style={{ flex: 1, minWidth: 260 }}>
          <h1 style={{ margin: "0 0 6px" }}>{product.name}</h1>
          <div className="muted">
            {product.brand} · {product.category}
          </div>
          <p className="muted">{product.description}</p>
          {best && (
            <div className="price" style={{ fontSize: 28 }}>
              {formatPrice(best.price, best.currency)}
              <span className="muted" style={{ fontSize: 14, marginLeft: 8 }}>
                best of {product.offer_count} sources
              </span>
            </div>
          )}
          {analytics && analytics.sample_size > 0 && <DealBadges a={analytics} />}
        </div>
      </div>

      <section className="panel">
        <h2>Price comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Price</th>
              <th>Availability</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {product.offers.map((o, i) => (
              <tr key={o.source} className={i === 0 ? "best" : ""}>
                <td style={{ textTransform: "capitalize" }}>
                  {o.source}
                  {i === 0 && (
                    <span className="badge" style={{ marginLeft: 8 }}>
                      cheapest
                    </span>
                  )}
                </td>
                <td className="price" style={{ fontSize: 16 }}>
                  {formatPrice(o.price, o.currency)}
                </td>
                <td className="muted">{o.in_stock ? "In stock" : "Out of stock"}</td>
                <td>
                  <a href={o.url} target="_blank" rel="noreferrer">
                    View deal →
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Price history</h2>
          <div className="row" style={{ gap: 6 }}>
            {RANGES.map((r) => (
              <button
                key={r.label}
                type="button"
                className="secondary"
                onClick={() => setDays(r.days)}
                style={{
                  padding: "6px 12px",
                  fontSize: 13,
                  borderColor: days === r.days ? "var(--accent)" : undefined,
                  color: days === r.days ? "var(--accent)" : undefined,
                }}
              >
                {r.label}
              </button>
            ))}
            <button
              type="button"
              className="secondary"
              onClick={() => setChartMode(chartMode === "best" ? "source" : "best")}
              style={{ padding: "6px 12px", fontSize: 13 }}
              title="Toggle best-price vs per-source view"
            >
              {chartMode === "best" ? "Best price" : "Per source"}
            </button>
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          {history ? (
            <PriceChart points={history.points} mode={chartMode} />
          ) : (
            <div className="muted">Loading…</div>
          )}
        </div>
        <div className="row" style={{ gap: 12, marginTop: 12 }}>
          <span className="muted">Export:</span>
          <a href={api.historyExportUrl(product.id, "csv", days)}>CSV</a>
          <a href={api.historyExportUrl(product.id, "json", days)}>JSON</a>
        </div>
      </section>

      <section className="panel">
        <h2>Set a price alert</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Get an email when the best price drops below your target.
        </p>
        <AlertForm
          productId={product.id}
          currency={best?.currency || "USD"}
          suggested={best?.price ?? null}
        />
        <div style={{ marginTop: 20, borderTop: "1px solid var(--border)", paddingTop: 16 }}>
          <AlertManager />
        </div>
      </section>
    </main>
  );
}

// Deal score (F020) and price-vs-average badges (F021).
function DealBadges({ a }: { a: PriceAnalytics }) {
  const score = a.deal_score ?? 0;
  const scoreColor = score >= 70 ? "var(--accent-2)" : score >= 40 ? "var(--accent)" : "var(--muted)";
  const pct = a.pct_vs_avg ?? 0;
  const belowAvg = pct < 0;
  return (
    <div className="row" style={{ gap: 8, marginTop: 10 }}>
      <span
        className="badge"
        title="100 = at the historical low for this window"
        style={{ borderColor: scoreColor, color: scoreColor }}
      >
        Deal score {score}/100
      </span>
      <span
        className="badge"
        title="Current best price vs the window average"
        style={{ color: belowAvg ? "var(--accent-2)" : "var(--danger)" }}
      >
        {belowAvg ? "▼" : "▲"} {Math.abs(pct).toFixed(1)}% vs avg
      </span>
      {a.min_price != null && (
        <span className="badge" title="Lowest price seen in this window">
          Low {formatPrice(a.min_price, a.currency)}
        </span>
      )}
    </div>
  );
}
