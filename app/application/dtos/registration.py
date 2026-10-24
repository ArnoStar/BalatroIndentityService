from dataclasses import dataclass
from uuid import UUID

from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.password import Password


@dataclass(frozen=True)
class RegisterUserInput:
    email: Email
    password: Password
    display_name: DisplayName


@dataclass(frozen=True)
class RegisterUserOutput:
    user_id: UUID


@dataclass(frozen=True)
class ConfirmEmailInput:
    email: Email
    code: str


@dataclass(frozen=True)
class ResendConfirmationInput:
    email: Email
