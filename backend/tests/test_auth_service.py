"""Unit tests for AuthService and WatchlistService (F035–F040)."""
import pytest

from app.core.security import hash_password, verify_password
from app.domain.schemas import PreferencesUpdate
from app.services.auth_service import (
    AuthService,
    EmailTakenError,
    InvalidCredentialsError,
)
from app.services.price_service import ProductNotFoundError
from app.services.watchlist_service import WatchlistService


# ── password hashing ──

def test_password_hash_roundtrip():
    h = hash_password("s3cret-password")
    assert h != "s3cret-password"
    assert verify_password("s3cret-password", h)
    assert not verify_password("wrong", h)


# ── auth ──

@pytest.mark.asyncio
async def test_register_and_login(auth_repo):
    service = AuthService(auth_repo)

    reg = await service.register("a@example.com", "password123")
    assert reg.token
    assert reg.user.email == "a@example.com"
    assert reg.user.default_currency == "USD"

    login = await service.login("a@example.com", "password123")
    assert login.token
    # A fresh session token is issued per login.
    assert login.token != reg.token


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_repo):
    service = AuthService(auth_repo)
    await service.register("dup@example.com", "password123")
    with pytest.raises(EmailTakenError):
        await service.register("dup@example.com", "password123")


@pytest.mark.asyncio
async def test_login_wrong_password(auth_repo):
    service = AuthService(auth_repo)
    await service.register("b@example.com", "password123")
    with pytest.raises(InvalidCredentialsError):
        await service.login("b@example.com", "nope")


@pytest.mark.asyncio
async def test_authenticate_token(auth_repo):
    service = AuthService(auth_repo)
    reg = await service.register("c@example.com", "password123")

    user = await service.authenticate(reg.token)
    assert user is not None and user.email == "c@example.com"
    assert await service.authenticate("garbage") is None
    assert await service.authenticate(None) is None


@pytest.mark.asyncio
async def test_logout_invalidates_token(auth_repo):
    service = AuthService(auth_repo)
    reg = await service.register("d@example.com", "password123")
    await service.logout(reg.token)
    assert await service.authenticate(reg.token) is None


@pytest.mark.asyncio
async def test_update_preferences(auth_repo):
    service = AuthService(auth_repo)
    reg = await service.register("e@example.com", "password123")
    user = await service.authenticate(reg.token)

    out = await service.update_preferences(
        user, PreferencesUpdate(default_currency="eur", default_sort="name")
    )
    assert out.default_currency == "EUR"
    assert out.default_sort == "name"


# ── watchlist ──

@pytest.mark.asyncio
async def test_watchlist_add_list_remove(auth_repo, watchlist_repo, product_repo):
    auth = AuthService(auth_repo)
    reg = await auth.register("w@example.com", "password123")
    user = await auth.authenticate(reg.token)

    product = await product_repo.upsert_product(
        slug="p", name="P", brand=None, category=None, description=None, image_url=None
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=50.0, currency="USD", in_stock=True
    )

    service = WatchlistService(watchlist_repo, product_repo)
    await service.add(user.id, product.id)
    await service.add(user.id, product.id)  # idempotent

    items = await service.list_items(user.id, currency="EUR")
    assert len(items) == 1
    assert items[0].name == "P"
    assert items[0].best_price == 46.0  # 50 USD -> EUR
    assert items[0].currency == "EUR"

    assert await service.remove(user.id, product.id) is True
    assert await service.list_items(user.id) == []


@pytest.mark.asyncio
async def test_watchlist_add_missing_product(auth_repo, watchlist_repo, product_repo):
    auth = AuthService(auth_repo)
    reg = await auth.register("w2@example.com", "password123")
    user = await auth.authenticate(reg.token)

    service = WatchlistService(watchlist_repo, product_repo)
    with pytest.raises(ProductNotFoundError):
        await service.add(user.id, 9999)
