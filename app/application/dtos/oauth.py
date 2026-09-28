from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.token_pair import TokenPair
from app.domain.value_object.email import Email
from app.domain.value_object.oauth_provider import OAuthProvider


@dataclass(frozen=True)
class OAuthIdentity:
    provider: OAuthProvider
    provider_user_id: str
    email: Email


@dataclass(frozen=True)
class InitiateOAuthInput:
    provider: OAuthProvider


@dataclass(frozen=True)
class InitiateOAuthOutput:
    state: str
    callback_url: str


@dataclass(frozen=True)
class AuthenticateOAuthInput:
    provider: OAuthProvider
    state: str
    code: str


@dataclass(frozen=True)
class AuthenticateOAuthOutput:
    token_pair: TokenPair


@dataclass(frozen=True)
class UnlinkOAuthAccountInput:
    user_id: UUID
    provider: OAuthProvider
