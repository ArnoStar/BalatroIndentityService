from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.application.dtos.roles import ListAccountsInput, SetRolesInput
from app.domain.value_object.role import Role
from app.presentation.api.dependencies import AppContainer, CurrentUserId, Uses
from app.presentation.api.schemas.admin import (
    AccountsPageResponse,
    AccountSummaryResponse,
    RoleResponse,
    SetRolesRequest,
)

router = APIRouter(tags=["Roles"])


@router.get("/roles", summary="The roles an account can have")
def list_roles(container: AppContainer) -> list[RoleResponse]:
    """Access tokens name the account's roles (``roles``); each service
    decides what a role allows there."""
    return [RoleResponse.of(r) for r in container.list_roles.execute()]


@router.get("/admin/accounts", summary="Find accounts (admins)")
async def list_accounts(
    user_id: CurrentUserId,
    uses: Uses,
    query: Annotated[str | None, Query(max_length=320)] = None,
    role: Role | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AccountsPageResponse:
    """Accounts whose email or display name contains ``query``, with ``role``
    if given, oldest first. 403 ``forbidden`` without the admin role."""
    page = await uses.list_accounts.execute(
        ListAccountsInput(user_id, query or None, role, limit, offset)
    )
    return AccountsPageResponse.of(page)


@router.put(
    "/admin/accounts/{account_id}/roles", summary="Set an account's roles (admins)"
)
async def set_roles(
    account_id: UUID, body: SetRolesRequest, user_id: CurrentUserId, uses: Uses
) -> AccountSummaryResponse:
    """The account's roles become these. Its access tokens name them from its
    next refresh. 409 ``last_admin`` when it would leave no admin."""
    account = await uses.set_account_roles.execute(
        SetRolesInput(user_id, account_id, frozenset(body.roles))
    )
    return AccountSummaryResponse.of(account)
