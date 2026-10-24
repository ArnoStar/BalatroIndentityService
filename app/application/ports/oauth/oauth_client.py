from typing import Protocol

from app.application.dtos.oauth import OAuthIdentity
from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthClient(Protocol):
    """The OAuth 2 / OpenID Connect providers the server is configured for."""

    def providers(self) -> list[OAuthProvider]: ...

    def authorization_url(
        self,
        provider: OAuthProvider,
        state: str,
        code_challenge: str,
        redirect_uri: str,
    ) -> str: ...

    async def exchange(
        self,
        provider: OAuthProvider,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> OAuthIdentity:
        """Raises OAuthExchangeFailed."""
        ...
