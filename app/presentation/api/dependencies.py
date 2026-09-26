from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.container import RequestContainer
from app.infrastructure.sqlalchemy.sqlalchemy import get_db


async def get_container(
    session: AsyncSession = Depends(get_db),
) -> RequestContainer:
    return RequestContainer(session)
