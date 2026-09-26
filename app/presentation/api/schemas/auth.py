from uuid import UUID

from pydantic import BaseModel, EmailStr


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
