from httpx import AsyncClient

from app.application.dtos.oauth import OAuthIdentity
from app.application.ports.oauth.oauth_account_issuer import OAuthAccountIssuer
from app.domain.value_object.email import Email
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.config.settings import settings


class HttpxOAuthAccountIssuer(OAuthAccountIssuer):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def issue(
        self,
        provider: OAuthProvider,
        code: str,
    ) -> OAuthIdentity:
        self.provider = provider
        match provider:
            case OAuthProvider.GOOGLE:
                return await self._issue_google(code)
            case _:
                raise ValueError(f"Unsupported OAuth provider: {provider}")

    async def _issue_google(self, code: str) -> OAuthIdentity:
        response = await self.client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()

        tokens = response.json()

        response = await self.client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
            },
        )
        response.raise_for_status()

        userinfo = response.json()

        return OAuthIdentity(
            provider=self.provider,
            provider_user_id=userinfo["sub"],
            email=Email(userinfo["email"]),
        )
