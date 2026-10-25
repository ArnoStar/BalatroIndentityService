"""Roles: who may do what beyond playing. Only admins see the accounts and
change roles; the last admin can't lose the role (nobody could give it back
but the command line)."""

import logging
from uuid import UUID

from app.application.dtos.roles import (
    AccountsPage,
    AccountSummary,
    ListAccountsInput,
    RoleInfo,
    SetRolesInput,
)
from app.application.exceptions.roles import LastAdmin, NotAllowed
from app.application.exceptions.user import UserDoesntExist
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User
from app.domain.value_object.role import ROLE_DESCRIPTIONS, Role

log = logging.getLogger(__name__)


async def require_admin(user_repo: UserRepo, actor_id: UUID) -> User:
    """The acting account, if it is an admin (now, in the database: not as an
    older access token says)."""
    actor = await user_repo.get_by_id(actor_id)
    if actor is None or Role.ADMIN not in actor.roles:
        raise NotAllowed
    return actor


def summary(user: User) -> AccountSummary:
    return AccountSummary(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified,
        roles=sorted(user.roles),
        created_at=user.created_at,
    )


class ListRoles:
    def execute(self) -> list[RoleInfo]:
        return [RoleInfo(role, ROLE_DESCRIPTIONS[role]) for role in Role]


class ListAccounts:
    def __init__(self, user_repo: UserRepo) -> None:
        self.user_repo = user_repo

    async def execute(self, dto: ListAccountsInput) -> AccountsPage:
        await require_admin(self.user_repo, dto.actor_id)
        users, total = await self.user_repo.search(
            dto.query, dto.role, dto.limit, dto.offset
        )
        return AccountsPage([summary(u) for u in users], total)


class SetAccountRoles:
    """The account's roles become the given ones. They are in its access
    tokens from the next refresh (at most the access token's lifetime)."""

    def __init__(self, user_repo: UserRepo, unit_of_work: UnitOfWork) -> None:
        self.user_repo = user_repo
        self.unit_of_work = unit_of_work

    async def execute(self, dto: SetRolesInput) -> AccountSummary:
        if dto.actor_id is not None:
            await require_admin(self.user_repo, dto.actor_id)
        user = await self.user_repo.get_by_id(dto.user_id)
        if user is None:
            raise UserDoesntExist
        if (
            Role.ADMIN in user.roles
            and Role.ADMIN not in dto.roles
            and await self.user_repo.count_with_role(Role.ADMIN) <= 1
        ):
            raise LastAdmin
        await self.user_repo.set_roles(user.id, dto.roles, granted_by=dto.actor_id)
        await self.unit_of_work.commit()
        log.info(
            "roles of account %s: %s -> %s (by %s)",
            user.id,
            sorted(user.roles),
            sorted(dto.roles),
            dto.actor_id or "the command line",
        )
        updated = await self.user_repo.get_by_id(user.id)
        assert updated is not None
        return summary(updated)
