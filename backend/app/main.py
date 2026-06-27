"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, auth, products, search
from app.core.config import get_settings
from app.core.database import init_db
from app.seed import seed_on_startup

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed demo data on startup."""
    await init_db()
    if settings.seed_on_startup:
        await seed_on_startup()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "MyDealFinder — a price search engine. Search products, compare prices "
        "across sources, view price history, and set price alerts."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(products.router)
app.include_router(alerts.router)
app.include_router(auth.router)


@app.get("/config", tags=["meta"], summary="Public client configuration & feature flags")
async def config() -> dict[str, object]:
    """Expose the active feature flags so the frontend can adapt its UI."""
    return {"feature_flags": settings.feature_flags}


@app.get("/health", tags=["meta"], summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@app.get("/", tags=["meta"], summary="API root")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }
