from typing import Protocol

from app.application.dtos.oauth import OAuthIdentity
from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthAccountIssuer(Protocol):
    async def issue(self, provider: OAuthProvider, code: str) -> OAuthIdentity: ...
