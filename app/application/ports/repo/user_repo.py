from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User
from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.role import Role


class UserRepo(Protocol):
    async def create(self, user: User) -> None:
        """Raises UserAlreadyExist when the email is taken."""
        ...

    async def get_by_id(self, id: UUID) -> User | None: ...
    async def get_by_email(self, email: Email) -> User | None: ...
    async def verify_email(self, user_id: UUID, verified_at: datetime) -> None: ...
    async def set_display_name(
        self, user_id: UUID, display_name: DisplayName
    ) -> None: ...
    async def delete_by_id(self, id: UUID) -> None:
        """Also deletes the user's password and linked accounts."""
        ...

    async def set_roles(
        self, user_id: UUID, roles: frozenset[Role], granted_by: UUID | None
    ) -> None:
        """The account's roles become ``roles`` (the ones it keeps keep their
        record of who gave them)."""
        ...

    async def count_with_role(self, role: Role) -> int: ...

    async def search(
        self, query: str | None, role: Role | None, limit: int, offset: int
    ) -> tuple[list[User], int]:
        """Accounts whose email or display name contains ``query`` (any case),
        with ``role`` if given, oldest first; and how many there are."""
        ...
