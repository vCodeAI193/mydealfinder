"""Shared pytest fixtures: an in-memory database and repositories per test."""
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base
from app.domain import models  # noqa: F401  (register models on metadata)
from app.repositories.alert_repository import AlertRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.watchlist_repository import WatchlistRepository


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """A fresh in-memory SQLite database for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
def product_repo(session: AsyncSession) -> ProductRepository:
    return ProductRepository(session)


@pytest_asyncio.fixture
def price_repo(session: AsyncSession) -> PriceRepository:
    return PriceRepository(session)


@pytest_asyncio.fixture
def alert_repo(session: AsyncSession) -> AlertRepository:
    return AlertRepository(session)


@pytest_asyncio.fixture
def auth_repo(session: AsyncSession) -> AuthRepository:
    return AuthRepository(session)


@pytest_asyncio.fixture
def watchlist_repo(session: AsyncSession) -> WatchlistRepository:
    return WatchlistRepository(session)
