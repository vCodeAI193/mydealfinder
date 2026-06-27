"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, formatPrice, type WatchlistItem } from "@/lib/api";
import { isLoggedIn, onAuthChange } from "@/lib/auth";
import { getCurrency, onPrefsChange } from "@/lib/prefs";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [authed, setAuthed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!isLoggedIn()) {
      setAuthed(false);
      setItems(null);
      return;
    }
    setAuthed(true);
    api
      .watchlist(getCurrency())
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load watchlist"));
  }, []);

  useEffect(() => {
    load();
    const offAuth = onAuthChange(load);
    const offPrefs = onPrefsChange(load);
    return () => {
      offAuth();
      offPrefs();
    };
  }, [load]);

  async function remove(productId: number) {
    await api.removeFromWatchlist(productId);
    setItems((prev) => prev?.filter((i) => i.product_id !== productId) ?? null);
  }

  if (!authed) {
    return (
      <main>
        <div className="empty">
          Please <Link href="/account">log in</Link> to view your watchlist.
        </div>
      </main>
    );
  }

  return (
    <main>
      <h1>Your watchlist</h1>
      {error && <div className="notice err">{error}</div>}
      {items && items.length === 0 && (
        <div className="empty">
          Nothing saved yet. Open a product and tap “♥ Save” to track it.
        </div>
      )}
      {items && items.length > 0 && (
        <div className="grid">
          {items.map((item) => (
            <div key={item.product_id} className="card">
              <Link href={`/product/${item.product_id}`} style={{ color: "inherit" }}>
                {item.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img className="thumb" src={item.image_url} alt={item.name} />
                )}
                <div className="body">
                  <div className="name">{item.name}</div>
                  <div style={{ flex: 1 }} />
                  <div className="price">{formatPrice(item.best_price, item.currency)}</div>
                </div>
              </Link>
              <button
                type="button"
                className="secondary"
                style={{ margin: 12, marginTop: 0 }}
                onClick={() => remove(item.product_id)}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
