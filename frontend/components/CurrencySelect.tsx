"use client";

import { useEffect, useState } from "react";
import { CURRENCIES, getCurrency, setCurrency } from "@/lib/prefs";

// Header currency selector (F012). Persists to localStorage and broadcasts the
// change so the search and product pages re-fetch converted prices.
export default function CurrencySelect() {
  const [currency, setCur] = useState("USD");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setCur(getCurrency());
    setMounted(true);
  }, []);

  return (
    <select
      aria-label="Display currency"
      value={mounted ? currency : "USD"}
      onChange={(e) => {
        setCur(e.target.value);
        setCurrency(e.target.value);
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
