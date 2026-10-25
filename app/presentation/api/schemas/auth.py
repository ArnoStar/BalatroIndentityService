"""Request and response bodies. Field names are the JSON names."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.application.dtos.authentication import AccountOutput
from app.application.dtos.tokens import TokenPair
from app.domain.value_object.oauth_provider import OAuthProvider
from app.domain.value_object.role import Role

# (the rules themselves are the domain's; these only bound the input size)
PasswordField = Field(min_length=1, max_length=1024)
CodeField = Field(min_length=1, max_length=32)
NameField = Field(min_length=1, max_length=64)


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = PasswordField
    display_name: str = NameField


class RegisterUserResponse(BaseModel):
    user_id: UUID
    email_verification_required: bool = True


class ConfirmEmailRequest(BaseModel):
    email: EmailStr
    code: str = CodeField


class EmailRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = PasswordField


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="seconds until the access token expires")

    @classmethod
    def of(cls, tokens: TokenPair) -> "TokenResponse":
        return cls(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = CodeField
    password: str = PasswordField


class AccountResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    email_verified: bool
    has_password: bool
    providers: list[OAuthProvider]
    created_at: datetime
    roles: list[Role]

    @classmethod
    def of(cls, account: AccountOutput) -> "AccountResponse":
        return cls(
            id=account.id,
            email=account.email.value,
            display_name=account.display_name.value,
            email_verified=account.email_verified,
            has_password=account.has_password,
            providers=account.providers,
            created_at=account.created_at,
            roles=account.roles,
        )


class UpdateAccountRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
