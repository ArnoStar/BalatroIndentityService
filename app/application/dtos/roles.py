from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.role import Role


@dataclass(frozen=True)
class RoleInfo:
    role: Role
    description: str


@dataclass(frozen=True)
class ListAccountsInput:
    actor_id: UUID
    query: str | None = None
    role: Role | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class AccountSummary:
    id: UUID
    email: Email
    display_name: DisplayName
    email_verified: bool
    roles: list[Role]
    created_at: datetime


@dataclass(frozen=True)
class AccountsPage:
    accounts: list[AccountSummary]
    total: int


@dataclass(frozen=True)
class SetRolesInput:
    actor_id: UUID | None  # None: the command line (python -m app.manage)
    user_id: UUID
    roles: frozenset[Role]
