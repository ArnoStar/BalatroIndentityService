"""Roles and the admins' view of the accounts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dtos.roles import AccountsPage, AccountSummary, RoleInfo
from app.domain.value_object.role import Role


class RoleResponse(BaseModel):
    role: Role
    description: str

    @classmethod
    def of(cls, info: RoleInfo) -> "RoleResponse":
        return cls(role=info.role, description=info.description)


class AccountSummaryResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    email_verified: bool
    roles: list[Role]
    created_at: datetime

    @classmethod
    def of(cls, a: AccountSummary) -> "AccountSummaryResponse":
        return cls(
            id=a.id,
            email=a.email.value,
            display_name=a.display_name.value,
            email_verified=a.email_verified,
            roles=a.roles,
            created_at=a.created_at,
        )


class AccountsPageResponse(BaseModel):
    accounts: list[AccountSummaryResponse]
    total: int

    @classmethod
    def of(cls, page: AccountsPage) -> "AccountsPageResponse":
        return cls(
            accounts=[AccountSummaryResponse.of(a) for a in page.accounts],
            total=page.total,
        )


class SetRolesRequest(BaseModel):
    roles: list[Role] = Field(max_length=len(Role))
