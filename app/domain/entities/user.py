from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.role import Role


@dataclass
class User:
    id: UUID
    email: Email
    display_name: DisplayName
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    roles: frozenset[Role] = field(default_factory=frozenset)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None
