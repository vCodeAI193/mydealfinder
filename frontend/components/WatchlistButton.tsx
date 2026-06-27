"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { isLoggedIn, onAuthChange } from "@/lib/auth";

// Save/remove a product from the watchlist (F037). Prompts guests to log in.
export default function WatchlistButton({ productId }: { productId: number }) {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const sync = () => {
      const loggedIn = isLoggedIn();
      setAuthed(loggedIn);
      if (loggedIn) {
        api
          .watchlist()
          .then((items) => setSaved(items.some((i) => i.product_id === productId)))
          .catch(() => {});
      } else {
        setSaved(false);
      }
    };
    sync();
    return onAuthChange(sync);
  }, [productId]);

  async function toggle() {
    if (!authed) {
      router.push("/account");
      return;
    }
    setBusy(true);
    try {
      if (saved) {
        await api.removeFromWatchlist(productId);
        setSaved(false);
      } else {
        await api.addToWatchlist(productId);
        setSaved(true);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      className={saved ? "" : "secondary"}
      onClick={toggle}
      disabled={busy}
      title={authed ? "" : "Log in to save"}
    >
      {saved ? "♥ Saved" : "♡ Save to watchlist"}
    </button>
  );
}
