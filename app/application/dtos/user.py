from dataclasses import dataclass

from app.domain.value_object.email import Email


@dataclass(frozen=True)
class RegisterUserDTO:
    email: Email
