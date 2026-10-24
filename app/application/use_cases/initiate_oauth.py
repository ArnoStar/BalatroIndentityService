import base64
import hashlib
import secrets
from collections.abc import Collection

from app.application.dtos.oauth import (
    InitiateOAuthInput,
    InitiateOAuthOutput,
    PendingOAuthLogin,
)
from app.application.exceptions.oauth import (
    OAuthProviderNotConfigured,
    RedirectUriNotAllowed,
)
from app.application.ports.oauth.oauth_client import OAuthClient
from app.application.ports.oauth.oauth_state_store import OAuthStateStore
from app.domain.value_object.oauth_provider import OAuthProvider


class ListOAuthProviders:
    def __init__(self, oauth_client: OAuthClient) -> None:
        self.oauth_client = oauth_client

    def execute(self) -> list[OAuthProvider]:
        return self.oauth_client.providers()


class InitiateOAuth:
    """Starts an authorization code flow (with PKCE): the client sends the
    browser to ``authorization_url``; the provider sends it back to
    ``redirect_uri`` with a code and the state, which the client gives to
    AuthenticateOAuth."""

    def __init__(
        self,
        oauth_client: OAuthClient,
        oauth_state_store: OAuthStateStore,
        allowed_redirect_uris: Collection[str],
    ) -> None:
        self.oauth_client = oauth_client
        self.oauth_state_store = oauth_state_store
        self.allowed_redirect_uris = allowed_redirect_uris

    async def execute(self, dto: InitiateOAuthInput) -> InitiateOAuthOutput:
        if dto.provider not in self.oauth_client.providers():
            raise OAuthProviderNotConfigured

        if dto.redirect_uri not in self.allowed_redirect_uris:
            raise RedirectUriNotAllowed

        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

        await self.oauth_state_store.save(
            state,
            PendingOAuthLogin(dto.provider, dto.redirect_uri, code_verifier),
        )

        return InitiateOAuthOutput(
            state=state,
            authorization_url=self.oauth_client.authorization_url(
                dto.provider, state, code_challenge, dto.redirect_uri
            ),
        )
