"use client";

import { useEffect, useState } from "react";
import { CURRENCIES, getCurrency, setCurrency } from "@/lib/prefs";
import { isLoggedIn } from "@/lib/auth";
import { api } from "@/lib/api";

// Header currency selector (F012). Persists to localStorage and broadcasts the
// change so the search and product pages re-fetch converted prices.
export default function CurrencySelect() {
  const [currency, setCur] = useState("USD");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setCur(getCurrency());
    setMounted(true);
    // Keep in sync if login adopts a different saved currency.
    const onStorage = () => setCur(getCurrency());
    window.addEventListener("prefschange", onStorage);
    return () => window.removeEventListener("prefschange", onStorage);
  }, []);

  return (
    <select
      aria-label="Display currency"
      value={mounted ? currency : "USD"}
      onChange={(e) => {
        const value = e.target.value;
        setCur(value);
        setCurrency(value);
        // Persist as a preference for signed-in users (F038).
        if (isLoggedIn()) api.updatePreferences({ default_currency: value }).catch(() => {});
      }}
      style={{ width: "auto", padding: "6px 10px", fontSize: 13 }}
    >
      {CURRENCIES.map((c) => (
        <option key={c} value={c}>
          {c}
        </option>
      ))}
    </select>
  );
}
