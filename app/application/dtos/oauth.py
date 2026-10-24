from dataclasses import dataclass
from uuid import UUID

from app.domain.value_object.email import Email
from app.domain.value_object.oauth_provider import OAuthProvider


@dataclass(frozen=True)
class OAuthIdentity:
    """Who the provider says signed in."""

    provider: OAuthProvider
    provider_user_id: str
    email: Email
    email_verified: bool


@dataclass(frozen=True)
class PendingOAuthLogin:
    """Kept server side between the redirect to the provider and its callback."""

    provider: OAuthProvider
    redirect_uri: str
    code_verifier: str  # PKCE


@dataclass(frozen=True)
class InitiateOAuthInput:
    provider: OAuthProvider
    redirect_uri: str


@dataclass(frozen=True)
class InitiateOAuthOutput:
    state: str
    authorization_url: str


@dataclass(frozen=True)
class AuthenticateOAuthInput:
    provider: OAuthProvider
    state: str
    code: str


@dataclass(frozen=True)
class UnlinkOAuthAccountInput:
    user_id: UUID
    provider: OAuthProvider
