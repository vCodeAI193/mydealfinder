"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, type FeatureFlags, type User } from "@/lib/api";
import { clearLocalSession, getStoredUser, onAuthChange, setStoredUser } from "@/lib/auth";
import { CURRENCIES } from "@/lib/prefs";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "de", label: "Deutsch" },
  { code: "fr", label: "Français" },
  { code: "es", label: "Español" },
];

const SORTS = [
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "name", label: "Name (A–Z)" },
];

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [flags, setFlags] = useState<FeatureFlags | null>(null);
  const [saved, setSaved] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setUser(getStoredUser());
    setMounted(true);
    api.config().then((c) => setFlags(c.feature_flags)).catch(() => {});
    return onAuthChange(() => setUser(getStoredUser()));
  }, []);

  async function savePref(patch: Partial<Pick<User, "default_currency" | "default_sort" | "language">>) {
    const updated = await api.updatePreferences(patch);
    setUser(updated);
    setStoredUser(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  async function exportData() {
    const data = await api.exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mydealfinder-data.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function deleteAccount() {
    if (!confirm("Delete your account and all data? This cannot be undone.")) return;
    await api.deleteAccount();
    clearLocalSession();
    router.push("/");
  }

  if (!mounted) return null;

  if (!user) {
    return (
      <main>
        <div className="empty">
          Please <Link href="/account">log in</Link> to manage your settings.
        </div>
      </main>
    );
  }

  return (
    <main>
      <h1>Settings</h1>

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Profile</h2>
        <p className="muted">Signed in as <strong>{user.email}</strong></p>
      </section>

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Preferences</h2>
        <div className="row">
          <div className="field">
            <label>Default currency (F038)</label>
            <select
              value={user.default_currency}
              onChange={(e) => savePref({ default_currency: e.target.value })}
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Default sort (F040)</label>
            <select
              value={user.default_sort}
              onChange={(e) => savePref({ default_sort: e.target.value })}
            >
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Language (F039)</label>
            <select
              value={user.language}
              onChange={(e) => savePref({ language: e.target.value })}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
        {saved && <div className="notice ok">Preferences saved.</div>}
      </section>

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Your data</h2>
        <div className="row">
          {flags?.enable_data_export !== false && (
            <button type="button" className="secondary" onClick={exportData}>
              Export my data (JSON)
            </button>
          )}
          {flags?.enable_account_deletion !== false && (
            <button
              type="button"
              onClick={deleteAccount}
              style={{ background: "var(--danger)" }}
            >
              Delete account
            </button>
          )}
        </div>
        <p className="muted" style={{ fontSize: 13, marginBottom: 0 }}>
          Export downloads everything we store about you. Deletion removes your
          account, watchlist, preferences, and alerts permanently.
        </p>
      </section>
    </main>
  );
}
