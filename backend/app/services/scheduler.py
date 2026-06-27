"""In-process background scheduler (F084).

Runs the price refresh (F046) and alert evaluation on configurable intervals
using asyncio tasks started/stopped with the app lifespan. Each job opens its
own database session and is resilient to errors so one failure does not stop the
loop. For multi-worker / distributed deployments this would move to Celery or a
dedicated worker — the job functions here are written to port directly.
"""
import asyncio

from app.core import metrics
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.repositories.alert_repository import AlertRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services.alert_service import AlertService
from app.services.refresh_service import RefreshService
from app.sources import get_default_sources

logger = get_logger("scheduler")


async def run_refresh_job() -> None:
    async with AsyncSessionLocal() as session:
        service = RefreshService(
            get_default_sources(), ProductRepository(session), PriceRepository(session)
        )
        count = await service.refresh_all()
        await session.commit()
        logger.info("Refreshed prices for %d product(s)", count)


async def run_alert_job() -> None:
    async with AsyncSessionLocal() as session:
        service = AlertService(AlertRepository(session), ProductRepository(session))
        result = await service.check_alerts()
        await session.commit()
        if result.triggered:
            logger.info("Alert check triggered %d alert(s)", len(result.triggered))


class Scheduler:
    """Manages the background job loops."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    async def _loop(self, name: str, job, interval: int) -> None:
        logger.info("Scheduler job '%s' started (every %ss)", name, interval)
        while True:
            try:
                await asyncio.sleep(interval)
                await job()
                metrics.inc("mydealfinder_scheduler_runs_total")
            except asyncio.CancelledError:
                break
            except Exception:  # never let a job error kill the loop
                logger.exception("Scheduler job '%s' failed", name)

    def start(self) -> None:
        settings = get_settings()
        if not settings.scheduler_enabled:
            logger.info("Scheduler disabled")
            return
        if settings.refresh_interval_seconds > 0:
            self._tasks.append(
                asyncio.create_task(
                    self._loop("refresh", run_refresh_job, settings.refresh_interval_seconds)
                )
            )
        if settings.alert_check_interval_seconds > 0:
            self._tasks.append(
                asyncio.create_task(
                    self._loop("alerts", run_alert_job, settings.alert_check_interval_seconds)
                )
            )

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
