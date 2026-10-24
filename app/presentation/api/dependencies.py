from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.authentication import CheckTokenInput
from app.application.exceptions.token import InvalidToken
from app.bootstrap.container import Container, RequestContainer

bearer = HTTPBearer(auto_error=False, description="an access token")


def get_app_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


AppContainer = Annotated[Container, Depends(get_app_container)]


async def get_session(container: AppContainer) -> AsyncGenerator[AsyncSession]:
    # what isn't committed by the use case is rolled back when it closes
    async with container.sessionmaker() as session:
        yield session


async def get_container(
    container: AppContainer,
    # ("function": the session closes before the response is sent)
    session: Annotated[AsyncSession, Depends(get_session, scope="function")],
) -> RequestContainer:
    return container.request(session)


Uses = Annotated[RequestContainer, Depends(get_container)]


def get_current_user_id(
    container: AppContainer,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UUID:
    if credentials is None:
        raise InvalidToken("an access token is required (Authorization: Bearer)")
    output = container.check_user_token.execute(
        CheckTokenInput(credentials.credentials)
    )
    return output.user_id


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
