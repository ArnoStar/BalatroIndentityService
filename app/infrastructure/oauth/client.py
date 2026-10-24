import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from app.application.dtos.oauth import OAuthIdentity
from app.application.exceptions.oauth import (
    OAuthExchangeFailed,
    OAuthProviderNotConfigured,
)
from app.application.ports.oauth.oauth_client import OAuthClient
from app.domain.exceptions import InvalidEmail
from app.domain.value_object.email import Email
from app.domain.value_object.oauth_provider import OAuthProvider

log = logging.getLogger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class HttpxOAuthClient(OAuthClient):
    """Google's OpenID Connect, with PKCE. A provider is enabled when its
    client id and secret are set."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        google_client_id: str | None,
        google_client_secret: str | None,
    ) -> None:
        self.http = http
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret

    def providers(self) -> list[OAuthProvider]:
        if self.google_client_id and self.google_client_secret:
            return [OAuthProvider.GOOGLE]
        return []

    def _check(self, provider: OAuthProvider) -> None:
        if provider not in self.providers():
            raise OAuthProviderNotConfigured

    def authorization_url(
        self,
        provider: OAuthProvider,
        state: str,
        code_challenge: str,
        redirect_uri: str,
    ) -> str:
        self._check(provider)
        query = urlencode(
            {
                "client_id": self.google_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email",
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        )
        return f"{GOOGLE_AUTHORIZE_URL}?{query}"

    async def exchange(
        self,
        provider: OAuthProvider,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> OAuthIdentity:
        self._check(provider)
        try:
            response = await self.http.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
            )
            response.raise_for_status()
            tokens: dict[str, Any] = response.json()

            response = await self.http.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            response.raise_for_status()
            userinfo: dict[str, Any] = response.json()

            return OAuthIdentity(
                provider=provider,
                provider_user_id=str(userinfo["sub"]),
                email=Email(userinfo["email"]),
                email_verified=userinfo.get("email_verified") is True,
            )
        except (httpx.HTTPError, KeyError, ValueError, InvalidEmail) as exc:
            log.warning("Google sign-in failed: %r", exc)
            raise OAuthExchangeFailed from exc
