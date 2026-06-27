"use client";

// Client-side display preferences shared across pages: currency (F012) and
// pinned sources (F013). Changes broadcast a "prefschange" event so any mounted
// page can refetch with the new preference.

export const CURRENCIES = ["USD", "EUR", "GBP", "CHF", "JPY", "CAD"] as const;
const PREFS_EVENT = "prefschange";

function emit() {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(PREFS_EVENT));
}

export function getCurrency(): string {
  if (typeof window === "undefined") return "USD";
  return localStorage.getItem("currency") || "USD";
}

export function setCurrency(currency: string) {
  localStorage.setItem("currency", currency);
  emit();
}

export function getDefaultSort(): string {
  if (typeof window === "undefined") return "price_asc";
  return localStorage.getItem("defaultSort") || "price_asc";
}

export function setDefaultSort(sort: string) {
  // No broadcast: the default sort is read when a new search starts, so it does
  // not need to trigger a refetch of the current results.
  localStorage.setItem("defaultSort", sort);
}

export function getPinnedSources(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem("pinnedSources") || "[]");
  } catch {
    return [];
  }
}

export function togglePinnedSource(source: string) {
  const current = new Set(getPinnedSources());
  if (current.has(source)) current.delete(source);
  else current.add(source);
  localStorage.setItem("pinnedSources", JSON.stringify([...current]));
  emit();
}

export function onPrefsChange(handler: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(PREFS_EVENT, handler);
  return () => window.removeEventListener(PREFS_EVENT, handler);
}
