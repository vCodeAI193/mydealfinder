"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStoredUser, logout, onAuthChange } from "@/lib/auth";
import type { User } from "@/lib/api";

// Header account widget (F035/F036): shows login/register link for guests,
// or the user's email with watchlist + logout when signed in.
export default function AuthWidget() {
  const [user, setUser] = useState<User | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const sync = () => setUser(getStoredUser());
    sync();
    setMounted(true);
    return onAuthChange(sync);
  }, []);

  if (!mounted) return null;

  if (!user) {
    return (
      <Link href="/account" className="badge" style={{ alignSelf: "center" }}>
        Log in
      </Link>
    );
  }

  return (
    <div className="row" style={{ gap: 8, alignItems: "center" }}>
      {user.is_admin && (
        <Link href="/admin" className="badge" title="Admin dashboard">
          ⚙ Admin
        </Link>
      )}
      <Link href="/watchlist" className="badge" title="Your watchlist">
        ♥ Watchlist
      </Link>
      <Link href="/settings" className="muted" style={{ fontSize: 13 }} title={user.email}>
        {user.email.split("@")[0]}
      </Link>
      <button
        type="button"
        className="secondary"
        style={{ padding: "6px 10px", fontSize: 13 }}
        onClick={() => logout()}
      >
        Log out
      </button>
    </div>
  );
}
