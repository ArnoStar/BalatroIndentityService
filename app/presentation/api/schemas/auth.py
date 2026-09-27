from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr


class OAuthProv(StrEnum):
    GOOGLE = "google"


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterUserResponse(BaseModel):
    user_id: UUID


class AuthenticateUserRequest(BaseModel):
    email: EmailStr
    password: str


class AuthenticateUserResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class InitiateOAuthRequest(BaseModel):
    provider: OAuthProv


class InitiateOAuthResponse(BaseModel):
    state: str
    callback_url: str


class AuthenticateOAuthRequest(BaseModel):
    state: str
    code: str


class AuthenticateOAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
