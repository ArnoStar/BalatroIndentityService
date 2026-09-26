from fastapi import APIRouter, Depends

from app.application.dtos.authentication import AuthUserInput, AuthUserOutput
from app.application.dtos.registration import RegisterUserInput, RegisterUserOutput
from app.bootstrap.container import RequestContainer
from app.domain.value_object.email import Email
from app.presentation.api.dependencies import get_container
from app.presentation.api.schemas.auth import (
    AuthenticateUserRequest,
    AuthenticateUserResponse,
    RegisterUserRequest,
    RegisterUserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterUserResponse)
async def register_user(
    request: RegisterUserRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: RegisterUserInput = RegisterUserInput(
        email=Email(request.email), password=request.password
    )

    user: RegisterUserOutput = await container.register_user.execute(dto)

    return RegisterUserResponse(user_id=user.user_id)


@router.post("/authenticate", response_model=AuthenticateUserResponse)
async def authenticate_user(
    request: AuthenticateUserRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: AuthUserInput = AuthUserInput(
        email=Email(request.email), password=request.password
    )

    tokens: AuthUserOutput = await container.authenticate_user.execute(dto)

    return AuthenticateUserResponse(
        access_token=tokens.token_pair.access_token.value,
        refresh_token=tokens.token_pair.refresh_token.value,
    )
