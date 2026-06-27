"""FastAPI dependency wiring: build services from a request-scoped session."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.alert_repository import AlertRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services.alert_service import AlertService
from app.services.price_service import PriceService
from app.services.search_service import SearchService
from app.sources import get_default_sources

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_search_service(session: SessionDep) -> SearchService:
    return SearchService(
        sources=get_default_sources(),
        product_repo=ProductRepository(session),
        price_repo=PriceRepository(session),
    )


def get_price_service(session: SessionDep) -> PriceService:
    return PriceService(
        product_repo=ProductRepository(session),
        price_repo=PriceRepository(session),
    )


def get_alert_service(session: SessionDep) -> AlertService:
    return AlertService(
        alert_repo=AlertRepository(session),
        product_repo=ProductRepository(session),
    )


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
PriceServiceDep = Annotated[PriceService, Depends(get_price_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
