from uuid import UUID

from aio_pika.abc import AbstractChannel
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.authentication import CheckTokenInput, CheckTokenOutput
from app.bootstrap.container import RequestContainer
from app.domain.value_object.tokens import AccessToken
from app.infrastructure.httpx.httpx import get_httpx_client
from app.infrastructure.rabbitmq.rabbitmq import get_rabbitmq_chanel
from app.infrastructure.sqlalchemy.sqlalchemy import get_db

bearer = HTTPBearer()


async def get_container(
    session: AsyncSession = Depends(get_db),
    httpx_client: AsyncClient = Depends(get_httpx_client),
    rabbitmq_chanel: AbstractChannel = Depends(get_rabbitmq_chanel),
) -> RequestContainer:
    return RequestContainer(session, httpx_client, rabbitmq_chanel)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    container: RequestContainer = Depends(get_container),
) -> UUID:
    dto: CheckTokenInput = CheckTokenInput(AccessToken(credentials.credentials))

    user_id: CheckTokenOutput = container.check_user_token.execute(dto)

    return user_id.user_id
