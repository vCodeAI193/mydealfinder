"""FastAPI dependency wiring: build services from a request-scoped session."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.domain.models import User
from app.core.config import get_settings
from app.repositories.alert_repository import AlertRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.account_service import AccountService
from app.services.admin_service import AdminService
from app.services.alert_service import AlertService
from app.services.audit_service import AuditService
from app.services.cache import Cache
from app.services.auth_service import AuthService
from app.services.price_service import PriceService
from app.services.refresh_service import RefreshService
from app.services.search_service import SearchService
from app.services.watchlist_service import WatchlistService
from app.sources import get_default_sources

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_search_service(session: SessionDep) -> SearchService:
    return SearchService(
        sources=get_default_sources(),
        product_repo=ProductRepository(session),
        price_repo=PriceRepository(session),
        cache=Cache(),
    )


def get_price_service(session: SessionDep) -> PriceService:
    return PriceService(
        product_repo=ProductRepository(session),
        price_repo=PriceRepository(session),
    )


def get_refresh_service(session: SessionDep) -> RefreshService:
    return RefreshService(
        get_default_sources(), ProductRepository(session), PriceRepository(session)
    )


def get_alert_service(session: SessionDep) -> AlertService:
    return AlertService(
        alert_repo=AlertRepository(session),
        product_repo=ProductRepository(session),
    )


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(AuthRepository(session))


def get_watchlist_service(session: SessionDep) -> WatchlistService:
    return WatchlistService(WatchlistRepository(session), ProductRepository(session))


def get_account_service(session: SessionDep) -> AccountService:
    return AccountService(
        auth_repo=AuthRepository(session),
        alert_repo=AlertRepository(session),
        watchlist_service=WatchlistService(WatchlistRepository(session), ProductRepository(session)),
    )


def get_audit_service(session: SessionDep) -> AuditService:
    return AuditService(AuditRepository(session))


def get_admin_service(session: SessionDep) -> AdminService:
    return AdminService(session, AuditService(AuditRepository(session)))


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
PriceServiceDep = Annotated[PriceService, Depends(get_price_service)]
RefreshServiceDep = Annotated[RefreshService, Depends(get_refresh_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
WatchlistServiceDep = Annotated[WatchlistService, Depends(get_watchlist_service)]
AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]


def _token_from_header(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


async def get_optional_user(
    auth: AuthServiceDep, authorization: str | None = Header(default=None)
) -> User | None:
    """Resolve the current user from a bearer token, or None for guests (F036)."""
    return await auth.authenticate(_token_from_header(authorization))


async def get_current_user(
    auth: AuthServiceDep, authorization: str | None = Header(default=None)
) -> User:
    """Require an authenticated user; 401 otherwise."""
    user = await auth.authenticate(_token_from_header(authorization))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_admin_user(
    auth: AuthServiceDep, authorization: str | None = Header(default=None)
) -> User:
    """Require an authenticated user whose email is in ADMIN_EMAILS (F079)."""
    user = await auth.authenticate(_token_from_header(authorization))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.email.lower() not in get_settings().admin_email_list:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]
