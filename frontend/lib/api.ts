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
  shipping_cost: number;
  total_price: number;
  currency: string;
  in_stock: boolean;
  source_rating: number | null;
  coupon_code: string | null;
  coupon_savings: number;
  pinned: boolean;
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
  window_days: number | null;
  points: PricePoint[];
}

export interface PriceAnalytics {
  product_id: number;
  window_days: number | null;
  sample_size: number;
  currency: string | null;
  current_price: number | null;
  min_price: number | null;
  max_price: number | null;
  avg_price: number | null;
  pct_vs_avg: number | null;
  deal_score: number | null;
}

export interface SearchResponse {
  query: string;
  count: number;
  page: number;
  page_size: number;
  results: ProductSummary[];
}

export interface SearchOptions {
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  sort?: "price_asc" | "price_desc" | "name";
  in_stock_only?: boolean;
  currency?: string;
  page?: number;
  page_size?: number;
}

export interface FeatureFlags {
  fuzzy_search: boolean;
  enabled_sources: string[];
  true_price: boolean;
  show_source_ratings: boolean;
  show_coupons: boolean;
  allow_guest: boolean;
  enable_data_export: boolean;
  enable_account_deletion: boolean;
}

export interface Alert {
  id: number;
  product_id: number;
  email: string;
  alert_type: "absolute" | "percentage";
  threshold_price: number | null;
  threshold_pct: number | null;
  reference_price: number | null;
  effective_threshold: number | null;
  currency: string;
  recurring: boolean;
  status: "active" | "paused" | "triggered";
  active: boolean;
  armed: boolean;
  created_at: string;
  triggered_at: string | null;
  triggered_price: number | null;
}

export interface AlertCreate {
  product_id: number;
  email: string;
  alert_type: "absolute" | "percentage";
  threshold_price?: number;
  threshold_pct?: number;
  recurring?: boolean;
  currency: string;
}

export interface AlertSuggestion {
  product_id: number;
  current_price: number | null;
  avg_price: number | null;
  suggested_threshold: number | null;
  window_days: number | null;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
  default_currency: string;
  default_sort: string;
  language: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface WatchlistItem {
  product_id: number;
  slug: string;
  name: string;
  image_url: string | null;
  best_price: number | null;
  currency: string | null;
  added_at: string;
}

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(init?.headers || {}),
    },
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
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function buildSearchQuery(q: string, opts: SearchOptions = {}): string {
  const params = new URLSearchParams({ q });
  if (opts.category) params.set("category", opts.category);
  if (opts.brand) params.set("brand", opts.brand);
  if (opts.min_price != null) params.set("min_price", String(opts.min_price));
  if (opts.max_price != null) params.set("max_price", String(opts.max_price));
  if (opts.sort) params.set("sort", opts.sort);
  if (opts.in_stock_only != null) params.set("in_stock_only", String(opts.in_stock_only));
  if (opts.currency) params.set("currency", opts.currency);
  if (opts.page != null) params.set("page", String(opts.page));
  if (opts.page_size != null) params.set("page_size", String(opts.page_size));
  return params.toString();
}

export const api = {
  search: (q: string, opts: SearchOptions = {}) =>
    request<SearchResponse>(`/search?${buildSearchQuery(q, opts)}`),
  config: () => request<{ feature_flags: FeatureFlags }>(`/config`),
  product: (id: number, opts: { currency?: string; pinned?: string[] } = {}) => {
    const params = new URLSearchParams();
    if (opts.currency) params.set("currency", opts.currency);
    if (opts.pinned && opts.pinned.length) params.set("pinned", opts.pinned.join(","));
    const qs = params.toString();
    return request<ProductDetail>(`/products/${id}${qs ? `?${qs}` : ""}`);
  },
  history: (id: number, days?: number | null) =>
    request<PriceHistory>(`/products/${id}/history${days ? `?days=${days}` : ""}`),
  analytics: (id: number, days?: number | null) =>
    request<PriceAnalytics>(`/products/${id}/analytics${days ? `?days=${days}` : ""}`),
  historyExportUrl: (id: number, format: "csv" | "json", days?: number | null) => {
    const params = new URLSearchParams({ format });
    if (days) params.set("days", String(days));
    return `${API_URL}/products/${id}/history/export?${params.toString()}`;
  },
  createAlert: (body: AlertCreate) =>
    request<Alert>(`/alerts`, { method: "POST", body: JSON.stringify(body) }),
  listAlerts: (email: string) =>
    request<Alert[]>(`/alerts?email=${encodeURIComponent(email)}`),
  pauseAlert: (id: number) => request<Alert>(`/alerts/${id}/pause`, { method: "POST" }),
  resumeAlert: (id: number) => request<Alert>(`/alerts/${id}/resume`, { method: "POST" }),
  alertSuggestion: (productId: number, days = 30) =>
    request<AlertSuggestion>(`/alerts/suggestion?product_id=${productId}&days=${days}`),

  // Accounts (F035–F040)
  register: (email: string, password: string) =>
    request<AuthResponse>(`/auth/register`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>(`/auth/login`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<void>(`/auth/logout`, { method: "POST" }),
  me: () => request<User>(`/auth/me`),
  updatePreferences: (body: Partial<Pick<User, "default_currency" | "default_sort" | "language">>) =>
    request<User>(`/me/preferences`, { method: "PUT", body: JSON.stringify(body) }),
  watchlist: (currency?: string) =>
    request<WatchlistItem[]>(`/me/watchlist${currency ? `?currency=${currency}` : ""}`),
  addToWatchlist: (productId: number) =>
    request<{ status: string }>(`/me/watchlist`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId }),
    }),
  removeFromWatchlist: (productId: number) =>
    request<void>(`/me/watchlist/${productId}`, { method: "DELETE" }),
  exportData: () => request<unknown>(`/me/export`),
  deleteAccount: () => request<void>(`/me`, { method: "DELETE" }),
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
