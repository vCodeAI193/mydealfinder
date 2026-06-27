"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  api,
  formatPrice,
  type ProductSummary,
  type SearchOptions,
} from "@/lib/api";
import { getCurrency, onPrefsChange } from "@/lib/prefs";

const SUGGESTIONS = ["headphones", "iphone", "laptop", "switch", "kindle"];
const PAGE_SIZE = 12;

interface Filters {
  sort: NonNullable<SearchOptions["sort"]>;
  brand: string;
  category: string;
  minPrice: string;
  maxPrice: string;
  inStockOnly: boolean;
}

const DEFAULT_FILTERS: Filters = {
  sort: "price_asc",
  brand: "",
  category: "",
  minPrice: "",
  maxPrice: "",
  inStockOnly: true,
};

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [results, setResults] = useState<ProductSummary[] | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [brands, setBrands] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toOptions(f: Filters, p: number): SearchOptions {
    return {
      sort: f.sort,
      brand: f.brand || undefined,
      category: f.category || undefined,
      min_price: f.minPrice ? Number(f.minPrice) : undefined,
      max_price: f.maxPrice ? Number(f.maxPrice) : undefined,
      in_stock_only: f.inStockOnly,
      currency: getCurrency(),
      page: p,
      page_size: PAGE_SIZE,
    };
  }

  async function run(term: string, f: Filters, p: number) {
    const q = term.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.search(q, toOptions(f, p));
      setResults(res.results);
      setTotal(res.count);
      setPage(res.page);
      // Build facet options from the broadest view (no brand/category filter).
      if (!f.brand && !f.category) {
        setBrands(unique(res.results.map((r) => r.brand)));
        setCategories(unique(res.results.map((r) => r.category)));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  function onSearch(term: string) {
    const fresh = DEFAULT_FILTERS;
    setSubmitted(term);
    setFilters(fresh);
    setBrands([]);
    setCategories([]);
    run(term, fresh, 1);
  }

  // Re-run when filters change (but only once a search has been submitted).
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    if (submitted) run(submitted, filters, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  // Re-run the current search when the display currency changes (F012).
  useEffect(
    () => onPrefsChange(() => submitted && run(submitted, filters, page)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [submitted, filters, page]
  );

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main>
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          onSearch(query);
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
              onSearch(s);
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {results && (
        <div className="panel" style={{ marginTop: 0 }}>
          <div className="row">
            <div className="field">
              <label>Sort</label>
              <select
                value={filters.sort}
                onChange={(e) =>
                  setFilters({ ...filters, sort: e.target.value as Filters["sort"] })
                }
              >
                <option value="price_asc">Price: low to high</option>
                <option value="price_desc">Price: high to low</option>
                <option value="name">Name (A–Z)</option>
              </select>
            </div>
            <div className="field">
              <label>Brand</label>
              <select
                value={filters.brand}
                onChange={(e) => setFilters({ ...filters, brand: e.target.value })}
              >
                <option value="">All brands</option>
                {brands.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Category</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              >
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="field" style={{ maxWidth: 110 }}>
              <label>Min price</label>
              <input
                type="number"
                min="0"
                value={filters.minPrice}
                onChange={(e) => setFilters({ ...filters, minPrice: e.target.value })}
              />
            </div>
            <div className="field" style={{ maxWidth: 110 }}>
              <label>Max price</label>
              <input
                type="number"
                min="0"
                value={filters.maxPrice}
                onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
              />
            </div>
            <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={filters.inStockOnly}
                onChange={(e) => setFilters({ ...filters, inStockOnly: e.target.checked })}
                style={{ width: "auto" }}
              />
              <span className="muted">In stock only</span>
            </label>
          </div>
        </div>
      )}

      {error && <div className="notice err">{error}</div>}

      {results && results.length === 0 && !loading && (
        <div className="empty">No products match. Try another keyword or relax the filters.</div>
      )}

      {results && results.length > 0 && (
        <>
          <p className="muted" style={{ marginTop: 16 }}>
            {total} result{total === 1 ? "" : "s"} · page {page} of {totalPages}
          </p>
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

          {totalPages > 1 && (
            <div className="row" style={{ justifyContent: "center", marginTop: 24 }}>
              <button
                className="secondary"
                disabled={page <= 1 || loading}
                onClick={() => run(submitted, filters, page - 1)}
              >
                ← Prev
              </button>
              <span className="muted" style={{ alignSelf: "center" }}>
                {page} / {totalPages}
              </span>
              <button
                className="secondary"
                disabled={page >= totalPages || loading}
                onClick={() => run(submitted, filters, page + 1)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {!results && !loading && (
        <div className="empty">Search across multiple sources to find the best price.</div>
      )}
    </main>
  );
}

function unique(values: (string | null)[]): string[] {
  return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
}
