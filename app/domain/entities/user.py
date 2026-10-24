from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email


@dataclass
class User:
    id: UUID
    email: Email
    display_name: DisplayName
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None
