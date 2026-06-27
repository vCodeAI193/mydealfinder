"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStoredUser, login, register } from "@/lib/auth";

export default function AccountPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [user, setUser] = useState(getStoredUser());

  useEffect(() => setUser(getStoredUser()), []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") await register(email, password);
      else await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <main>
        <div className="panel">
          <h2 style={{ marginTop: 0 }}>You are signed in</h2>
          <p className="muted">Logged in as {user.email}.</p>
          <Link href="/watchlist">Go to your watchlist →</Link>
        </div>
      </main>
    );
  }

  return (
    <main>
      <div className="panel" style={{ maxWidth: 440, margin: "0 auto" }}>
        <div className="row" style={{ gap: 8, marginBottom: 16 }}>
          <button
            type="button"
            className={mode === "login" ? "" : "secondary"}
            onClick={() => setMode("login")}
          >
            Log in
          </button>
          <button
            type="button"
            className={mode === "register" ? "" : "secondary"}
            onClick={() => setMode("register")}
          >
            Register
          </button>
        </div>

        <form onSubmit={submit}>
          <div className="field" style={{ marginBottom: 12 }}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field" style={{ marginBottom: 16 }}>
            <label htmlFor="password">Password (min. 8 characters)</label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>

        {error && <div className="notice err">{error}</div>}

        <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
          No account needed to search and compare — signing in lets you save a
          watchlist and your preferences.
        </p>
      </div>
    </main>
  );
}
