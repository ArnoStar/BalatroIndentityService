from typing import Protocol

from app.application.dtos.oauth import PendingOAuthLogin


class OAuthStateStore(Protocol):
    async def save(self, state: str, pending: PendingOAuthLogin) -> None: ...
    async def pop(self, state: str) -> PendingOAuthLogin | None:
        """Each state works once."""
        ...
