from dataclasses import dataclass
from uuid import UUID

from app.domain.value_object.email import Email


@dataclass(frozen=True)
class RegisterUserInput:
    email: Email
    password: str


@dataclass(frozen=True)
class RegisterUserOutput:
    user_id: UUID


@dataclass(frozen=True)
class ConfirmEmailInput:
    email: Email
    code: str
