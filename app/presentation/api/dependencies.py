from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.authentication import CheckTokenInput, CheckTokenOutput
from app.bootstrap.container import RequestContainer
from app.domain.value_object.tokens import AccessToken
from app.infrastructure.httpx.httpx import get_httpx_client
from app.infrastructure.sqlalchemy.sqlalchemy import get_db

bearer = HTTPBearer()


async def get_container(
    session: AsyncSession = Depends(get_db),
    httpx_client: AsyncClient = Depends(get_httpx_client),
) -> RequestContainer:
    return RequestContainer(session, httpx_client)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    container: RequestContainer = Depends(get_container),
) -> UUID:
    dto: CheckTokenInput = CheckTokenInput(AccessToken(credentials.credentials))

    user_id: CheckTokenOutput = container.check_user_token.execute(dto)

    return user_id.user_id
