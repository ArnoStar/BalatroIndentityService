from dataclasses import dataclass
from uuid import UUID

from app.domain.value_object.email import Email
from app.domain.value_object.password_hash import PasswordHash


@dataclass
class User:
    id: UUID
    email: Email
    password_hash: PasswordHash
