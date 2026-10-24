from typing import Protocol
from uuid import UUID


class SessionStore(Protocol):
    """Sign-in sessions, each with one valid refresh token at a time."""

    async def create(self, user_id: UUID) -> str:
        """A new session; returns its refresh token."""
        ...

    async def rotate(self, refresh_token: str) -> tuple[UUID, str]:
        """Exchanges a refresh token for the next one of its session. A token
        used twice (stolen, or replayed) ends the session. Raises InvalidToken."""
        ...

    async def revoke(self, refresh_token: str) -> None: ...
    async def revoke_all(self, user_id: UUID) -> None: ...
