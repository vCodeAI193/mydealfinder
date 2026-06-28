# MyDealFinder — Configurable Feature Backlog

This is the living backlog of **configurable** capabilities MyDealFinder can
offer. Each feature is something a user (or operator) can **opt into** — it is
either a per-user **preference** or a global **feature flag**. Work through them
incrementally; flip a status box to `☑` when a feature ships.

> Today the MVP already implements the **baseline** below. The 100 items in this
> file are net-new features and enhancements on top of it.

**Baseline (already implemented):** keyword search · multi-source price
comparison · price history · one-shot price alerts · 3 mock sources.

---

## Legend

| Field | Values | Meaning |
|---|---|---|
| **Type** | `UP` · `FF` · `UP+FF` | `UP` = per-user preference · `FF` = global feature flag · `UP+FF` = both (flag enables it, user tunes it) |
| **Priority** | `P1` · `P2` · `P3` | `P1` high value / near-term · `P3` nice-to-have |
| **Effort** | `S` · `M` · `L` | rough size: small / medium / large |
| **Status** | `☐` · `☑` | todo / done |

**How "configurable" maps to code (target design, not yet built):**
- **FF** → boolean on `backend/app/core/config.py::Settings` (env-driven, same
  pattern as the existing `seed_on_startup`), later exposed via a read-only
  `/config` endpoint the frontend reads at startup.
- **UP** → a future per-user `preferences` store (a `user_preferences` table /
  JSON column) whose defaults come from `Settings`.

---

## 1. Search & Discovery

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F001 | Fuzzy / typo-tolerant search | FF | P1 | M | ☑ | Tolerate misspellings in `catalog.find_items` / search service |
| F002 | Search autocomplete & suggestions | FF | P2 | M | ☐ | `/search/suggest?q=` endpoint + dropdown in the search bar |
| F003 | Category & brand filters | UP | P1 | S | ☑ | Filter facets on search results |
| F004 | Price-range filter | UP | P1 | S | ☑ | Min/max price query params |
| F005 | Sort options (price, name, discount, popularity) | UP | P1 | S | ☑ | User-selectable result ordering |
| F006 | Results per page / pagination size | UP | P2 | S | ☑ | Configurable page size |
| F007 | Saved searches | UP | P2 | M | ☐ | Persist a query for one-click re-run |
| F008 | Recent search history | UP | P3 | S | ☐ | Local/per-user recent queries |
| F009 | Barcode / EAN lookup | FF | P3 | M | ☐ | Resolve a scanned code to a product |

## 2. Price Comparison

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F010 | Include / exclude out-of-stock offers | UP | P1 | S | ☑ | Toggle in the comparison table |
| F011 | Shipping-aware "true price" | FF | P1 | M | ☑ | Add shipping to offer total before ranking |
| F012 | Currency-converted display | UP | P2 | M | ☑ | Convert all offers to a chosen currency |
| F013 | Preferred / pinned sources | UP | P2 | S | ☑ | Always surface chosen retailers first |
| F014 | Per-source trust / rating badges | FF | P3 | S | ☑ | Reliability badge per source |
| F015 | Coupon / voucher code display | FF | P2 | M | ☑ | Show applicable discount codes |
| F016 | Tax & warranty cost notes | FF | P3 | M | ☐ | Total-cost-of-ownership annotations |

## 3. Price History & Analytics

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F017 | Selectable history time range (7/30/90/365d) | UP | P1 | S | ☑ | Range selector on the chart |
| F018 | Per-source vs best-price history toggle | UP | P2 | M | ☑ | Switch chart series |
| F019 | Min / max / average price markers | UP | P2 | S | ☑ | Reference lines on the chart |
| F020 | Historical "good deal" score | FF | P1 | M | ☑ | Score current price vs historical distribution |
| F021 | Price-drop percentage badges | UP | P2 | S | ☑ | "−18% vs 30-day avg" |
| F022 | Trend forecast | FF | P3 | L | ☐ | Simple projection of likely price direction |
| F023 | Export history (CSV / JSON) | FF | P3 | S | ☑ | Download endpoint for a product's history |
| F024 | Chart type (line / area / candlestick) | UP | P3 | M | ☐ | User-selectable visualization |

## 4. Alerts & Notifications

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F025 | Multiple alerts per product | FF | P1 | S | ☑ | Allow several thresholds per product |
| F026 | Percentage-drop alerts | UP | P1 | S | ☑ | Alert on % drop, not just absolute price |
| F027 | Back-in-stock alerts | FF | P2 | M | ☑ | Trigger when an out-of-stock offer returns |
| F028 | Email notification channel | UP | P1 | M | ☑ | Real SMTP delivery (replaces the log notifier) |
| F029 | Web push notifications | FF | P2 | L | ☐ | Browser push for triggered alerts |
| F030 | Chat webhook channel (Telegram/Slack/Discord) | FF | P3 | M | ☑ | Post alerts to a webhook URL |
| F031 | Alert frequency / digest (instant/daily/weekly) | UP | P2 | M | ☑ | Batch notifications |
| F032 | Snooze / pause alerts | UP | P2 | S | ☑ | Temporarily mute an alert |
| F033 | Recurring (re-arm) alerts | UP | P2 | S | ☑ | Re-activate after firing instead of one-shot |
| F034 | History-based target-price suggestions | FF | P3 | M | ☑ | Suggest a sensible threshold from history |

## 5. Accounts & Personalization

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F035 | User registration & login | FF | P1 | L | ☑ | Auth foundation for per-user data |
| F036 | Guest mode (no account) | FF | P1 | S | ☑ | Use the app without signing up |
| F037 | Watchlist / favorites | UP | P1 | M | ☑ | Save products to follow |
| F038 | Default currency preference | UP | P1 | S | ☑ | Per-user default currency |
| F039 | Default language preference | UP | P2 | S | ☑ | Per-user default UI language |
| F040 | Default sort / filter preferences | UP | P2 | S | ☑ | Remember preferred result view |
| F041 | Profile & settings page | FF | P2 | M | ☑ | Central place to manage preferences |
| F042 | GDPR data export | FF | P3 | M | ☑ | Download all personal data |
| F043 | Account deletion | FF | P2 | S | ☑ | Self-service account/data removal |

## 6. Data Sources & Scraping

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F044 | Real retailer scraper plugin | FF | P1 | L | ☑ | Implement `PriceSource` against a live site |
| F045 | Per-source enable / disable | FF | P1 | S | ☑ | Toggle sources in `get_default_sources` via config |
| F046 | Scheduled price-refresh interval | UP+FF | P1 | M | ☑ | Background refresh cadence |
| F047 | Source rate-limit config | FF | P2 | M | ☑ | Throttle requests per source |
| F048 | Manual "refresh now" button | UP | P2 | S | ☑ | On-demand re-fetch for a product |
| F049 | Source health dashboard | FF | P3 | M | ☑ | Show last-success / error per source |
| F050 | Add custom source via config | FF | P3 | M | ☑ | Register a source without code changes |

## 7. UI/UX, Theming & Accessibility

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F051 | Light / dark / system theme | UP | P1 | S | ☑ | Theme switch (CSS vars already in `globals.css`) |
| F052 | Accent color customization | UP | P3 | S | ☐ | User-chosen accent via CSS variables |
| F053 | Density (compact / comfortable) | UP | P3 | S | ☐ | Spacing preference |
| F054 | Grid vs list result view | UP | P2 | S | ☐ | Toggle search-results layout |
| F055 | Keyboard shortcuts | UP | P3 | M | ☐ | Quick search / navigation keys |
| F056 | High-contrast / reduced-motion mode | UP | P2 | S | ☐ | Accessibility toggles |
| F057 | Font-size scaling | UP | P3 | S | ☐ | Adjustable base font size |
| F058 | Localized number / currency formatting | UP | P2 | S | ☐ | Locale-aware `Intl` formatting |
| F059 | Onboarding tour | FF | P3 | M | ☐ | First-run walkthrough |
| F060 | Skeleton loaders & rich empty states | FF | P2 | S | ☐ | Better loading/empty UX |

## 8. Internationalization

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F061 | Multi-language UI (i18n) | UP+FF | P2 | L | ☐ | Translatable UI strings |
| F062 | Locale-aware date / time | UP | P2 | S | ☐ | Format timestamps per locale |
| F063 | Region-specific sources | UP | P3 | M | ☐ | Show sources relevant to a region |
| F064 | RTL language support | FF | P3 | M | ☐ | Right-to-left layout |
| F065 | Translatable catalog metadata | FF | P3 | M | ☐ | Localized product names/descriptions |

## 9. Sharing & Social

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F066 | Shareable product / comparison links | FF | P2 | S | ☐ | Stable share URLs |
| F067 | Share price-history snapshot image | FF | P3 | M | ☐ | Render chart to a shareable image |
| F068 | Public wishlists | FF | P3 | M | ☐ | Share a watchlist publicly |
| F069 | "Deal of the day" feed | FF | P2 | M | ☐ | Curated best current drops |
| F070 | Community price submissions | FF | P3 | L | ☐ | Users report prices they found |
| F071 | Upvote / flag deals | FF | P3 | M | ☐ | Community quality signals |

## 10. API & Integrations

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F072 | Public API keys | FF | P2 | M | ☐ | Issue keys for programmatic access |
| F073 | Outbound price-drop webhooks | FF | P2 | M | ☐ | POST to a user URL on trigger |
| F074 | Per-key rate limiting | FF | P2 | M | ☐ | Throttle API usage per key |
| F075 | RSS deal feed | FF | P3 | S | ☐ | Subscribe to deals via RSS |
| F076 | Browser-extension endpoint | FF | P3 | L | ☐ | API surface for an overlay extension |
| F077 | iCal feed for alert events | FF | P3 | S | ☐ | Calendar feed of triggered alerts |
| F078 | Zapier / IFTTT-style triggers | FF | P3 | M | ☐ | Generic automation triggers |

## 11. Admin & Ops

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F079 | Admin dashboard | FF | P2 | L | ☑ | Operator view of products/sources/alerts |
| F080 | Feature-flag management UI | FF | P2 | M | ☑ | Toggle the `FF` items at runtime |
| F081 | Audit log | FF | P3 | M | ☑ | Record significant actions |
| F082 | Log-level configuration | UP+FF | P2 | S | ☑ | Runtime/log verbosity (`DEBUG` already exists) |
| F083 | Prometheus metrics endpoint | FF | P3 | S | ☑ | `/metrics` for observability |
| F084 | Background job scheduler | FF | P1 | M | ☑ | Cron for refresh + `alerts/check` |

## 12. Performance & Caching

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F085 | Redis-backed search cache | FF | P2 | M | ☑ | Cache hot searches (`REDIS_URL` already wired) |
| F086 | Configurable cache TTL | UP+FF | P2 | S | ☑ | Tune cache lifetime |
| F087 | Pagination & response limits | UP | P2 | S | ☐ | Bound large responses |
| F088 | ETag / conditional requests | FF | P3 | M | ☐ | Cheap revalidation for clients |

## 13. Security & Privacy

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F089 | Rate limiting / abuse protection | FF | P1 | M | ☐ | Protect public endpoints |
| F090 | Email verification for alerts | FF | P2 | M | ☐ | Confirm ownership before alerting |
| F091 | Cookie-consent / privacy config | FF | P3 | S | ☐ | Configurable consent banner |
| F092 | Configurable data-retention period | UP+FF | P3 | M | ☐ | Auto-prune old history/alerts |
| F093 | API authentication (OAuth / JWT) | FF | P2 | L | ☐ | Token-based auth for the API |

## 14. AI & Smart Features

| ID | Feature | Type | Priority | Effort | Status | Notes |
|----|---------|------|----------|--------|--------|-------|
| F094 | Natural-language search | FF | P2 | L | ☐ | "noise-cancelling headphones under $200" |
| F095 | Smart cross-source product dedup/matching | FF | P1 | L | ☐ | Merge the same product across sources |
| F096 | "Is this a good deal?" assistant | FF | P3 | M | ☐ | Explain deal quality in plain language |
| F097 | Personalized recommendations | FF | P3 | L | ☐ | Suggest products from behavior |
| F098 | Auto-categorization of products | FF | P3 | M | ☐ | Infer category/brand automatically |
| F099 | Price-drop prediction model | FF | P3 | L | ☐ | Estimate likelihood/timing of a drop |
| F100 | Review-sentiment summary | FF | P3 | L | ☐ | Summarize review sentiment per product |

---

## Progress

**Overall: 51 / 100 complete.**

| Category | Range | Count | Done |
|---|---|---|---|
| 1. Search & Discovery | F001–F009 | 9 | 5 |
| 2. Price Comparison | F010–F016 | 7 | 6 |
| 3. Price History & Analytics | F017–F024 | 8 | 6 |
| 4. Alerts & Notifications | F025–F034 | 10 | 9 |
| 5. Accounts & Personalization | F035–F043 | 9 | 9 |
| 6. Data Sources & Scraping | F044–F050 | 7 | 7 |
| 7. UI/UX, Theming & Accessibility | F051–F060 | 10 | 1 |
| 8. Internationalization | F061–F065 | 5 | 0 |
| 9. Sharing & Social | F066–F071 | 6 | 0 |
| 10. API & Integrations | F072–F078 | 7 | 0 |
| 11. Admin & Ops | F079–F084 | 6 | 6 |
| 12. Performance & Caching | F085–F088 | 4 | 2 |
| 13. Security & Privacy | F089–F093 | 5 | 0 |
| 14. AI & Smart Features | F094–F100 | 7 | 0 |
| **Total** | **F001–F100** | **100** | **51** |

**Done so far:** F001 (fuzzy search), F003 (category/brand filters),
F004 (price-range filter), F005 (sort), F006 (pagination),
F010 (out-of-stock toggle), F011 (shipping "true price"), F012 (currency conversion),
F013 (pinned sources), F014 (source ratings), F015 (coupons),
F017 (history time range), F018 (per-source toggle),
F019 (min/max/avg markers), F020 (deal score), F021 (price-vs-avg badge),
F023 (CSV/JSON export), F025 (multiple alerts/limit), F026 (percentage-drop alerts),
F027 (back-in-stock), F028 (SMTP email), F030 (webhook channel), F031 (digest),
F032 (snooze/pause), F033 (recurring alerts), F034 (threshold suggestion),
F035 (registration/login), F036 (guest mode), F037 (watchlist),
F038 (default currency), F039 (default language), F040 (default sort),
F041 (settings page), F042 (GDPR export), F043 (account deletion),
F044 (real HTTP source), F045 (per-source enable/disable), F046 (scheduled refresh),
F047 (source rate-limit), F048 (manual refresh), F049 (source health), F050 (custom sources),
F051 (light/dark/system theme),
F079 (admin dashboard), F080 (feature-flag UI), F081 (audit log),
F082 (log-level config), F083 (Prometheus metrics), F084 (background scheduler),
F085 (Redis search cache), F086 (cache TTL).

**Only F029 (web push) remains in Alerts** — deferred as it needs a service
worker + VAPID, worth a dedicated effort.

### How to work through this backlog
1. Pick a feature by ID (e.g. "implement F037").
2. Implement it behind its `Type`: an `FF` gets a `Settings` flag; a `UP` gets a
   preference with a sensible default.
3. Flip its **Status** to `☑` and bump the **Done** counts above.
