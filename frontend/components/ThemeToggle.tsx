"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

const ORDER: Theme[] = ["system", "light", "dark"];
const LABEL: Record<Theme, string> = { system: "🖥 System", light: "☀ Light", dark: "🌙 Dark" };

// Resolve and apply the effective theme to <html data-theme>.
function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const effective =
    theme === "system"
      ? window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark"
      : theme;
  root.setAttribute("data-theme", effective);
}

// User-configurable theme preference (F051), persisted in localStorage.
export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = (localStorage.getItem("theme") as Theme) || "system";
    setTheme(saved);
    applyTheme(saved);
    setMounted(true);

    // Track OS changes while on "system".
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const onChange = () => {
      if ((localStorage.getItem("theme") as Theme) === "system") applyTheme("system");
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  function cycle() {
    const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
    setTheme(next);
    localStorage.setItem("theme", next);
    applyTheme(next);
  }

  // Avoid hydration mismatch: render a stable label until mounted.
  return (
    <button
      type="button"
      className="secondary"
      onClick={cycle}
      title="Switch theme"
      aria-label="Switch color theme"
      style={{ padding: "6px 12px", fontSize: 13 }}
    >
      {mounted ? LABEL[theme] : "🖥 System"}
    </button>
  );
}
