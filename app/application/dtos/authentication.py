from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.token_pair import TokenPair
from app.domain.value_object.email import Email
from app.domain.value_object.tokens import AccessToken, RefreshToken


@dataclass(frozen=True)
class AuthUserInput:
    email: Email
    password: str


@dataclass(frozen=True)
class AuthUserOutput:
    token_pair: TokenPair


@dataclass(frozen=True)
class RefreshTokenInput:
    refresh_token: RefreshToken


@dataclass(frozen=True)
class RefreshTokenOutput:
    token_pair: TokenPair


@dataclass(frozen=True)
class CheckTokenInput:
    access_token: AccessToken


@dataclass(frozen=True)
class CheckTokenOutput:
    user_id: UUID


@dataclass(frozen=True)
class DeleteUserInput:
    user_id: UUID
