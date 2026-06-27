import type { Metadata } from "next";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import CurrencySelect from "@/components/CurrencySelect";
import "./globals.css";

// Apply the saved theme before paint to avoid a flash of the wrong theme.
const noFlashThemeScript = `(function(){try{var t=localStorage.getItem('theme')||'system';var e=t==='system'?(window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'):t;document.documentElement.setAttribute('data-theme',e);}catch(_){}})();`;

export const metadata: Metadata = {
  title: "MyDealFinder — Compare prices, track deals",
  description:
    "Search products, compare prices across sources, view price history, and set price alerts.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlashThemeScript }} />
      </head>
      <body>
        <div className="container">
          <header className="header">
            <Link href="/" className="logo" style={{ textDecoration: "none" }}>
              My<span>Deal</span>Finder
            </Link>
            <span className="tagline">Compare prices · track history · get alerted</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              <CurrencySelect />
              <ThemeToggle />
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
