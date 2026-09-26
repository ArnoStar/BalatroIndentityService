from typing import Protocol

from app.domain.entities.oauth_account import OAuthAccount
from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthAccountRepo(Protocol):
    async def create(self, account: OAuthAccount) -> None: ...
    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> OAuthAccount | None: ...
