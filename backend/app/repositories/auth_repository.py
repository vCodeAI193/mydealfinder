"""Persistence for users and authentication sessions."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User, UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Users ──
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_user(self, *, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        return user

    async def delete_user(self, user: User) -> None:
        """Delete a user; sessions and watchlist cascade via the FK."""
        await self._session.delete(user)
        await self._session.flush()

    # ── Sessions ──
    async def add_session(self, *, user_id: int, token_hash: str) -> UserSession:
        sess = UserSession(user_id=user_id, token_hash=token_hash)
        self._session.add(sess)
        await self._session.flush()
        return sess

    async def get_user_by_token_hash(self, token_hash: str) -> User | None:
        result = await self._session.execute(
            select(User).join(UserSession).where(UserSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def delete_session(self, token_hash: str) -> None:
        result = await self._session.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        sess = result.scalar_one_or_none()
        if sess is not None:
            await self._session.delete(sess)
