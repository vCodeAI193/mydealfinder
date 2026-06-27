"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  formatPrice,
  type PriceHistory,
  type ProductDetail,
} from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import AlertForm from "@/components/AlertForm";

export default function ProductPage({ params }: { params: { id: string } }) {
  const productId = Number(params.id);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [history, setHistory] = useState<PriceHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [p, h] = await Promise.all([
          api.product(productId),
          api.history(productId),
        ]);
        if (!active) return;
        setProduct(p);
        setHistory(h);
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Failed to load product");
      }
    })();
    return () => {
      active = false;
    };
  }, [productId]);

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
        <h2>Price history</h2>
        {history ? <PriceChart points={history.points} /> : <div className="muted">Loading…</div>}
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
      </section>
    </main>
  );
}
