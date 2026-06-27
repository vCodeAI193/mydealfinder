"""Authentication and user-preference business logic (F035, F038–F040)."""
from app.core.security import (
    hash_password,
    hash_token,
    new_session_token,
    verify_password,
)
from app.domain.models import User
from app.domain.schemas import (
    AuthResponse,
    PreferencesUpdate,
    UserOut,
    UserPreferences,
)
from app.repositories.auth_repository import AuthRepository


class EmailTakenError(Exception):
    """Raised when registering an already-registered email."""


class InvalidCredentialsError(Exception):
    """Raised on a failed login."""


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    async def register(self, email: str, password: str) -> AuthResponse:
        if await self._repo.get_user_by_email(email) is not None:
            raise EmailTakenError(f"{email} is already registered")
        user = await self._repo.add_user(email=email, password_hash=hash_password(password))
        return await self._issue(user)

    async def login(self, email: str, password: str) -> AuthResponse:
        user = await self._repo.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        return await self._issue(user)

    async def logout(self, token: str) -> None:
        await self._repo.delete_session(hash_token(token))

    async def authenticate(self, token: str | None) -> User | None:
        """Resolve a bearer token to a user, or None if invalid/absent."""
        if not token:
            return None
        return await self._repo.get_user_by_token_hash(hash_token(token))

    async def update_preferences(self, user: User, update: PreferencesUpdate) -> UserOut:
        if update.default_currency is not None:
            user.default_currency = update.default_currency.upper()
        if update.default_sort is not None:
            user.default_sort = update.default_sort
        if update.language is not None:
            user.language = update.language
        return UserOut.model_validate(user)

    @staticmethod
    def preferences_of(user: User) -> UserPreferences:
        return UserPreferences.model_validate(user)

    async def _issue(self, user: User) -> AuthResponse:
        token = new_session_token()
        await self._repo.add_session(user_id=user.id, token_hash=hash_token(token))
        return AuthResponse(token=token, user=UserOut.model_validate(user))
