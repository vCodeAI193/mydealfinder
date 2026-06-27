# MyDealFinder

A modern price search engine that aggregates and compares deals across multiple
sources. Search a product, compare prices side by side, track how the price has
moved over time, and get alerted when it drops below your target.

> See [`VISION.md`](./VISION.md) for the product goals, tech-stack reasoning,
> architecture diagram, and roadmap. See [`FEATURES.md`](./FEATURES.md) for the
> 100-feature configurable backlog and what's already implemented.

---

## Features

| Feature | Endpoint(s) | UI |
|---|---|---|
| **Product search** | `GET /search?q=` | Home page |
| **Price comparison** | `GET /products/{id}`, `GET /products/{id}/offers` | Product page table |
| **Price history** | `GET /products/{id}/history` | Product page chart |
| **Price alerts** | `POST /alerts`, `GET /alerts?email=`, `POST /alerts/check` | Product page form |
| **Multi-source aggregation** | 3 pluggable mock sources (Amazon / eBay / Walmart-like) | — |

---

## Architecture

Layered / clean architecture in the backend:

```
API (FastAPI routers)
  → Services (business logic)
    → Repositories (SQLAlchemy persistence)
      → PostgreSQL / SQLite
Sources (pluggable PriceSource implementations) ← orchestrated by services
```

```
mydealfinder/
├── VISION.md
├── docker-compose.yml
├── .env.example
├── backend/                # FastAPI + SQLAlchemy (async)
│   ├── app/
│   │   ├── api/            # routers + dependency wiring
│   │   ├── core/           # config + database/session
│   │   ├── domain/         # ORM models + Pydantic schemas
│   │   ├── repositories/   # persistence layer
│   │   ├── services/       # business logic
│   │   ├── sources/        # pluggable price sources (mock catalog)
│   │   ├── seed.py         # demo data + 30 days of price history
│   │   └── main.py         # app entrypoint
│   └── tests/              # pytest unit tests
└── frontend/               # Next.js 14 (App Router) + TypeScript
    ├── app/                # pages (search, product detail)
    ├── components/         # PriceChart, AlertForm
    └── lib/api.ts          # typed API client
```

---

## Quick start (Docker — recommended)

Brings up Postgres, Redis, the API, and the web app together.

```bash
cp .env.example .env        # optional; sensible defaults are built in
docker compose up --build
```

Then open:

- **Web app:** http://localhost:3000
- **API + Swagger docs:** http://localhost:8000/docs
- **OpenAPI schema:** http://localhost:8000/openapi.json

The database is seeded with a demo catalog (headphones, phones, laptops, …) and
30 days of price history on first startup, so the UI has data immediately.

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs
```

By default the backend uses a local SQLite file (`mydealfinder.db`), so no
database server is required for development. Point `DATABASE_URL` at Postgres to
switch.

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

---

## Running the tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Unit tests cover the core business logic: search aggregation, price
comparison/history, alert evaluation, and catalog matching. They run against an
in-memory SQLite database — no external services needed.

---

## Try the API

```bash
# Search
curl "http://localhost:8000/search?q=headphones"

# Search with filters, sorting & pagination (F003–F006, F010)
curl "http://localhost:8000/search?q=apple&brand=Apple&min_price=200&max_price=300&sort=price_desc&page=1&page_size=12"

# Active feature flags (consumed by the frontend)
curl "http://localhost:8000/config"

# Compare prices for a product
curl "http://localhost:8000/products/1/offers"

# Price history (optionally windowed to the last N days — F017)
curl "http://localhost:8000/products/1/history?days=30"

# Price analytics: min/max/avg, deal score & price-vs-average (F019–F021)
curl "http://localhost:8000/products/1/analytics?days=30"

# Export price history as CSV or JSON (F023)
curl "http://localhost:8000/products/1/history/export?format=csv&days=30"

# Create a price alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"email":"you@example.com","threshold_price":300}'

# Evaluate alerts (a scheduler would call this on a cron in production)
curl -X POST http://localhost:8000/alerts/check
```

---

## Configuration

All configuration is via environment variables — see [`.env.example`](./.env.example).
Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite file | Async SQLAlchemy DSN |
| `REDIS_URL` | _(unset)_ | Optional cache; disabled when empty |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |
| `SEED_ON_STARTUP` | `true` | Seed demo data on first boot |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL for the browser |

---

## Extending with a real source

Adding a real retailer is a one-class change — implement `PriceSource.search()`
in `backend/app/sources/`, then register it in `get_default_sources()`. The
service layer, repositories, API, and UI need no changes because every source
returns the same normalized `SourceOffer` shape.
