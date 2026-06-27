"""Authentication and account endpoints (F035–F043)."""
import io

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import (
    AccountServiceDep,
    AuthServiceDep,
    CurrentUserDep,
    WatchlistServiceDep,
)
from app.core.config import get_settings
from app.domain.schemas import (
    AuthResponse,
    PreferencesUpdate,
    UserCredentials,
    UserOut,
    UserPreferences,
    WatchlistAdd,
    WatchlistItemOut,
)
from app.services.auth_service import EmailTakenError, InvalidCredentialsError
from app.services.price_service import ProductNotFoundError

router = APIRouter(tags=["accounts"])


@router.post("/auth/register", response_model=AuthResponse, status_code=201, summary="Register (F035)")
async def register(creds: UserCredentials, service: AuthServiceDep) -> AuthResponse:
    try:
        return await service.register(str(creds.email), creds.password)
    except EmailTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/auth/login", response_model=AuthResponse, summary="Log in (F035)")
async def login(creds: UserCredentials, service: AuthServiceDep) -> AuthResponse:
    try:
        return await service.login(str(creds.email), creds.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/auth/logout", status_code=204, summary="Log out")
async def logout(service: AuthServiceDep, authorization: str | None = Header(default=None)) -> None:
    if authorization and authorization.lower().startswith("bearer "):
        await service.logout(authorization[7:].strip())


@router.get("/auth/me", response_model=UserOut, summary="Current user")
async def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)


# ── Preferences (F038–F040) ──


@router.get("/me/preferences", response_model=UserPreferences, summary="Get preferences")
async def get_preferences(user: CurrentUserDep, service: AuthServiceDep) -> UserPreferences:
    return service.preferences_of(user)


@router.put("/me/preferences", response_model=UserOut, summary="Update preferences")
async def update_preferences(
    update: PreferencesUpdate, user: CurrentUserDep, service: AuthServiceDep
) -> UserOut:
    return await service.update_preferences(user, update)


# ── Watchlist (F037) ──


@router.get("/me/watchlist", response_model=list[WatchlistItemOut], summary="List watchlist")
async def list_watchlist(
    user: CurrentUserDep,
    service: WatchlistServiceDep,
    currency: str | None = Query(None, description="Convert best prices to this currency"),
) -> list[WatchlistItemOut]:
    return await service.list_items(user.id, currency=currency)


@router.post("/me/watchlist", status_code=201, summary="Add a product to the watchlist")
async def add_watchlist(payload: WatchlistAdd, user: CurrentUserDep, service: WatchlistServiceDep) -> dict:
    try:
        await service.add(user.id, payload.product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "added", "product_id": payload.product_id}


@router.delete("/me/watchlist/{product_id}", status_code=204, summary="Remove from the watchlist")
async def remove_watchlist(product_id: int, user: CurrentUserDep, service: WatchlistServiceDep) -> None:
    removed = await service.remove(user.id, product_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Not in watchlist")


# ── Data export (F042) & account deletion (F043) ──


@router.get("/me/export", summary="Export all of your data as JSON (F042)")
async def export_data(user: CurrentUserDep, service: AccountServiceDep):
    if not get_settings().enable_data_export:
        raise HTTPException(status_code=403, detail="Data export is disabled")
    import json

    data = await service.export_data(user)
    payload = json.dumps(data, indent=2).encode()
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="mydealfinder-data.json"'},
    )


@router.delete("/me", status_code=204, summary="Delete your account and all data (F043)")
async def delete_account(user: CurrentUserDep, service: AccountServiceDep) -> None:
    if not get_settings().enable_account_deletion:
        raise HTTPException(status_code=403, detail="Account deletion is disabled")
    await service.delete_account(user)
