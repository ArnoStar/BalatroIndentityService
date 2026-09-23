from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.email import Email


@dataclass
class User:
    id: UUID
    email: Email
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
