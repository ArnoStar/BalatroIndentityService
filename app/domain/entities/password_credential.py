from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.password_hash import PasswordHash


@dataclass
class PasswordCredential:
    user_id: UUID
    password_hash: PasswordHash
    created_at: datetime
    updated_at: datetime
