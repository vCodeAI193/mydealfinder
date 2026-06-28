"""Unit tests for admin/audit features (F079-F081)."""
import pytest

from app.core import flags
from app.repositories.audit_repository import AuditRepository
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService


@pytest.mark.asyncio
async def test_audit_record_and_list(session):
    service = AuditService(AuditRepository(session))
    await service.record(actor="a@example.com", action="user.login")
    await service.record(actor="b@example.com", action="alert.create", detail={"product_id": 1})

    entries = await service.list_recent()
    assert len(entries) == 2
    # Most recent first.
    assert entries[0].action == "alert.create"
    assert "product_id" in (entries[0].detail or "")


def test_flag_toggle_changes_settings(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "true_price", False)
    assert flags.current()["true_price"] is False

    flags.set_flag("true_price", True)
    assert get_settings().true_price is True
    assert flags.current()["true_price"] is True


def test_flag_toggle_rejects_unknown():
    with pytest.raises(KeyError):
        flags.set_flag("not_a_flag", True)


@pytest.mark.asyncio
async def test_admin_overview_counts(session, product_repo, alert_repo, auth_repo):
    from app.domain.schemas import AlertCreate
    from app.services.alert_service import AlertService
    from app.services.auth_service import AuthService

    product = await product_repo.upsert_product(
        slug="p", name="P", brand=None, category=None, description=None, image_url=None
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=10.0, currency="USD", in_stock=True
    )
    await AuthService(auth_repo).register("u@example.com", "password123")
    await AlertService(alert_repo, product_repo).create_alert(
        AlertCreate(product_id=product.id, email="u@example.com", threshold_price=5.0)
    )

    overview = await AdminService(session, AuditService(AuditRepository(session))).overview()

    assert overview.products == 1
    assert overview.offers == 1
    assert overview.users == 1
    assert overview.alerts_active == 1
    assert any(s["source"] == "amazon" for s in overview.sources)


def test_user_is_admin_from_config(monkeypatch):
    from app.core.config import get_settings
    from app.domain.models import User

    monkeypatch.setattr(get_settings(), "admin_emails", "boss@example.com")
    assert User(email="boss@example.com", password_hash="x").is_admin is True
    assert User(email="other@example.com", password_hash="x").is_admin is False
