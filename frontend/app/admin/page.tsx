"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type AdminOverview } from "@/lib/api";
import { getStoredUser, onAuthChange } from "@/lib/auth";

export default function AdminPage() {
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const user = getStoredUser();
    if (!user?.is_admin) {
      setAllowed(false);
      return;
    }
    setAllowed(true);
    Promise.all([api.adminOverview(), api.adminFlags()])
      .then(([o, f]) => {
        setOverview(o);
        setFlags(f);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, []);

  useEffect(() => {
    load();
    return onAuthChange(load);
  }, [load]);

  async function toggle(name: string) {
    const updated = await api.setAdminFlag(name, !flags[name]);
    setFlags(updated);
  }

  if (allowed === false) {
    return (
      <main>
        <div className="empty">
          Admins only. <Link href="/account">Log in</Link> with an admin account.
        </div>
      </main>
    );
  }

  return (
    <main>
      <h1>Admin dashboard</h1>
      {error && <div className="notice err">{error}</div>}

      {overview && (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Overview</h2>
          <div className="row" style={{ gap: 24 }}>
            <Stat label="Products" value={overview.products} />
            <Stat label="Offers" value={overview.offers} />
            <Stat label="Active alerts" value={overview.alerts_active} />
            <Stat label="Users" value={overview.users} />
          </div>
        </section>
      )}

      <section className="panel">
        <h2 style={{ marginTop: 0 }}>Feature flags</h2>
        <p className="muted" style={{ marginTop: 0 }}>Toggles take effect immediately.</p>
        <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
          {Object.entries(flags).map(([name, value]) => (
            <button
              key={name}
              type="button"
              className={value ? "" : "secondary"}
              onClick={() => toggle(name)}
              style={{ fontSize: 13 }}
            >
              {value ? "✓ " : "✗ "}
              {name}
            </button>
          ))}
        </div>
      </section>

      {overview && (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Source health</h2>
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Status</th>
                <th>OK</th>
                <th>Errors</th>
              </tr>
            </thead>
            <tbody>
              {overview.sources.map((s) => (
                <tr key={s.source}>
                  <td style={{ textTransform: "capitalize" }}>{s.source}</td>
                  <td><span className="badge">{s.status}</span></td>
                  <td className="muted">{s.ok_count}</td>
                  <td className="muted">{s.error_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {overview && (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Recent activity (audit log)</h2>
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {overview.recent_audit.map((e) => (
                <tr key={e.id}>
                  <td className="muted" style={{ fontSize: 12 }}>
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="muted">{e.actor}</td>
                  <td><span className="badge">{e.action}</span></td>
                  <td className="muted" style={{ fontSize: 12 }}>{e.detail || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>{value}</div>
      <div className="muted">{label}</div>
    </div>
  );
}
