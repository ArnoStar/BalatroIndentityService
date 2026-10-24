from typing import Protocol
from uuid import UUID

from app.domain.entities.oauth_account import OAuthAccount
from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthAccountRepo(Protocol):
    async def create(self, account: OAuthAccount) -> None: ...
    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> OAuthAccount | None: ...
    async def get_by_user_id(
        self,
        provider: OAuthProvider,
        user_id: UUID,
    ) -> OAuthAccount | None: ...
    async def get_providers(self, user_id: UUID) -> set[OAuthProvider]: ...
    async def delete_by_user_id(
        self,
        provider: OAuthProvider,
        user_id: UUID,
    ) -> bool:
        """False when there was nothing to delete."""
        ...
