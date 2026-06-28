"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alerts, auth, products, search, sources
from app.core import metrics
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.seed import seed_on_startup
from app.services.scheduler import Scheduler

setup_logging()
settings = get_settings()
scheduler = Scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables, seed demo data, and run the background scheduler."""
    await init_db()
    if settings.seed_on_startup:
        await seed_on_startup()
    scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


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
app.include_router(sources.router)


@app.get("/config", tags=["meta"], summary="Public client configuration & feature flags")
async def config() -> dict[str, object]:
    """Expose the active feature flags so the frontend can adapt its UI."""
    return {"feature_flags": settings.feature_flags}


@app.get("/metrics", tags=["meta"], summary="Prometheus metrics (F083)")
async def prometheus_metrics() -> Response:
    if not settings.enable_metrics:
        return Response(status_code=404)
    return Response(content=metrics.render(), media_type="text/plain; version=0.0.4")


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
