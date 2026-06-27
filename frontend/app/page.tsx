"use client";

import { useState } from "react";
import Link from "next/link";
import { api, formatPrice, type ProductSummary } from "@/lib/api";

const SUGGESTIONS = ["headphones", "iphone", "laptop", "switch", "kindle"];

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ProductSummary[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(q: string) {
    const term = q.trim();
    if (!term) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.search(term);
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          runSearch(query);
        }}
      >
        <input
          type="text"
          placeholder="Search for a product, e.g. 'headphones'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="row" style={{ marginBottom: 24 }}>
        <span className="muted">Try:</span>
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            className="secondary"
            onClick={() => {
              setQuery(s);
              runSearch(s);
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {error && <div className="notice err">{error}</div>}

      {results && results.length === 0 && !loading && (
        <div className="empty">No products found. Try another keyword.</div>
      )}

      {results && results.length > 0 && (
        <div className="grid">
          {results.map((p) => (
            <Link key={p.id} href={`/product/${p.id}`} className="card" style={{ color: "inherit" }}>
              {p.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img className="thumb" src={p.image_url} alt={p.name} />
              )}
              <div className="body">
                <div className="name">{p.name}</div>
                <div className="muted">{p.brand}</div>
                <div style={{ flex: 1 }} />
                <div className="price">{formatPrice(p.best_price, p.currency)}</div>
                <span className="badge">{p.offer_count} sources</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!results && !loading && (
        <div className="empty">
          Search across multiple sources to find the best price.
        </div>
      )}
    </main>
  );
}
