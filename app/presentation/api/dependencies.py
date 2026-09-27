from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.container import RequestContainer
from app.infrastructure.httpx.httpx import get_httpx_client
from app.infrastructure.sqlalchemy.sqlalchemy import get_db


async def get_container(
    session: AsyncSession = Depends(get_db),
    httpx_client: AsyncClient = Depends(get_httpx_client),
) -> RequestContainer:
    return RequestContainer(session, httpx_client)
