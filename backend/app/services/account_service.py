"""Account-level operations: data export (F042) and deletion (F043)."""
from app.domain.models import User
from app.domain.schemas import AlertOut, UserOut, UserPreferences
from app.repositories.alert_repository import AlertRepository
from app.repositories.auth_repository import AuthRepository
from app.services.watchlist_service import WatchlistService


class AccountService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        alert_repo: AlertRepository,
        watchlist_service: WatchlistService,
    ) -> None:
        self._auth = auth_repo
        self._alerts = alert_repo
        self._watchlist = watchlist_service

    async def export_data(self, user: User) -> dict:
        """Gather everything stored about a user for a GDPR export (F042)."""
        watchlist = await self._watchlist.list_items(user.id)
        alerts = await self._alerts.list_for_email(user.email)
        return {
            "profile": UserOut.model_validate(user).model_dump(mode="json"),
            "preferences": UserPreferences.model_validate(user).model_dump(mode="json"),
            "watchlist": [w.model_dump(mode="json") for w in watchlist],
            "alerts": [AlertOut.model_validate(a).model_dump(mode="json") for a in alerts],
        }

    async def delete_account(self, user: User) -> None:
        """Delete the user and all associated data (F043).

        Sessions and watchlist items cascade via their foreign keys; alerts are
        keyed by email, so they are removed explicitly.
        """
        await self._alerts.delete_for_email(user.email)
        await self._auth.delete_user(user)
