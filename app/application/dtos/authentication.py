from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.oauth_provider import OAuthProvider
from app.domain.value_object.password import Password
from app.domain.value_object.role import Role


@dataclass(frozen=True)
class AuthUserInput:
    email: Email
    password: str


@dataclass(frozen=True)
class RefreshTokenInput:
    refresh_token: str


@dataclass(frozen=True)
class LogoutInput:
    refresh_token: str


@dataclass(frozen=True)
class LogoutAllInput:
    user_id: UUID


@dataclass(frozen=True)
class CheckTokenInput:
    access_token: str


@dataclass(frozen=True)
class CheckTokenOutput:
    user_id: UUID


@dataclass(frozen=True)
class GetAccountInput:
    user_id: UUID


@dataclass(frozen=True)
class AccountOutput:
    id: UUID
    email: Email
    display_name: DisplayName
    email_verified: bool
    has_password: bool
    providers: list[OAuthProvider]
    created_at: datetime
    roles: list[Role]


@dataclass(frozen=True)
class DeleteUserInput:
    user_id: UUID


@dataclass(frozen=True)
class RequestPasswordResetInput:
    email: Email


@dataclass(frozen=True)
class ResetPasswordInput:
    email: Email
    code: str
    password: Password


@dataclass(frozen=True)
class UpdateAccountInput:
    user_id: UUID
    display_name: DisplayName | None = None
