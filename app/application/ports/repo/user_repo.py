from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User
from app.domain.value_object.email import Email


class UserRepo(Protocol):
    async def create(self, user: User) -> None: ...
    async def get_by_id(self, id: UUID) -> User | None: ...
    async def get_by_email(self, email: Email) -> User | None: ...
    async def verify_email(
        self,
        user_id: UUID,
        verified_at: datetime,
    ) -> None: ...
    async def delete_by_id(self, id: UUID) -> None: ...
