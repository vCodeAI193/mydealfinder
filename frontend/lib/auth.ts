"use client";

import { api, type User } from "@/lib/api";
import { setCurrency, setDefaultSort } from "@/lib/prefs";

// Client-side auth session (F035/F036). The token + cached user live in
// localStorage; an "authchange" event lets the header and pages react.
const AUTH_EVENT = "authchange";

function emit() {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(AUTH_EVENT));
}

export function getToken(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem("token");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("user");
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

function applySession(token: string, user: User) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
  // Adopt the user's saved preferences (F038/F040).
  setCurrency(user.default_currency);
  setDefaultSort(user.default_sort);
  emit();
}

export async function register(email: string, password: string): Promise<User> {
  const res = await api.register(email, password);
  applySession(res.token, res.user);
  return res.user;
}

export async function login(email: string, password: string): Promise<User> {
  const res = await api.login(email, password);
  applySession(res.token, res.user);
  return res.user;
}

export async function logout(): Promise<void> {
  try {
    await api.logout();
  } catch {
    /* best effort */
  }
  clearLocalSession();
}

/** Update the cached user (e.g. after changing preferences) and re-broadcast. */
export function setStoredUser(user: User) {
  localStorage.setItem("user", JSON.stringify(user));
  setCurrency(user.default_currency);
  setDefaultSort(user.default_sort);
  emit();
}

/** Drop the local session without a server round-trip (e.g. after deletion). */
export function clearLocalSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  emit();
}

export function onAuthChange(handler: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(AUTH_EVENT, handler);
  return () => window.removeEventListener(AUTH_EVENT, handler);
}
