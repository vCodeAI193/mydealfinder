// Typed client for the MyDealFinder backend API.
// All calls run in the browser, so we use the public API URL.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ProductSummary {
  id: number;
  slug: string;
  name: string;
  brand: string | null;
  category: string | null;
  image_url: string | null;
  best_price: number | null;
  currency: string | null;
  offer_count: number;
}

export interface Offer {
  source: string;
  url: string;
  price: number;
  currency: string;
  in_stock: boolean;
  updated_at: string;
}

export interface ProductDetail extends ProductSummary {
  description: string | null;
  offers: Offer[];
}

export interface PricePoint {
  source: string;
  price: number;
  currency: string;
  recorded_at: string;
}

export interface PriceHistory {
  product_id: number;
  points: PricePoint[];
}

export interface SearchResponse {
  query: string;
  count: number;
  results: ProductSummary[];
}

export interface Alert {
  id: number;
  product_id: number;
  email: string;
  threshold_price: number;
  currency: string;
  active: boolean;
  created_at: string;
  triggered_at: string | null;
  triggered_price: number | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  search: (q: string) =>
    request<SearchResponse>(`/search?q=${encodeURIComponent(q)}`),
  product: (id: number) => request<ProductDetail>(`/products/${id}`),
  history: (id: number) => request<PriceHistory>(`/products/${id}/history`),
  createAlert: (body: {
    product_id: number;
    email: string;
    threshold_price: number;
    currency: string;
  }) =>
    request<Alert>(`/alerts`, { method: "POST", body: JSON.stringify(body) }),
};

export function formatPrice(value: number | null, currency: string | null): string {
  if (value == null) return "—";
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency || ""}`.trim();
  }
}
