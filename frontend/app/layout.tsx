import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

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
      <body>
        <div className="container">
          <header className="header">
            <Link href="/" className="logo" style={{ textDecoration: "none" }}>
              My<span>Deal</span>Finder
            </Link>
            <span className="tagline">Compare prices · track history · get alerted</span>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
