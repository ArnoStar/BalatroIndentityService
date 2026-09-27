from typing import Protocol

from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthStateManager(Protocol):
    async def generate(self, provider: OAuthProvider) -> str: ...
    async def pop(self, state: str) -> OAuthProvider | None: ...
