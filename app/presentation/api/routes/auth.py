from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.dtos.authentication import (
    AuthUserInput,
    AuthUserOutput,
    ChangePasswordInput,
    DeleteUserInput,
    InitiateChangePasswordInput,
    RefreshTokenInput,
    RefreshTokenOutput,
)
from app.application.dtos.registration import (
    ConfirmEmailInput,
    RegisterUserInput,
    RegisterUserOutput,
)
from app.bootstrap.container import RequestContainer
from app.domain.value_object.email import Email
from app.domain.value_object.tokens import RefreshToken
from app.presentation.api.dependencies import get_container, get_current_user_id
from app.presentation.api.schemas.auth import (
    AuthenticateUserRequest,
    AuthenticateUserResponse,
    ChangePasswordRequest,
    ConfirmEmailRequest,
    InitiateChangePasswordRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
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


@router.post("/refresh-token", response_model=RefreshTokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: RefreshTokenInput = RefreshTokenInput(
        refresh_token=RefreshToken(request.refresh_token)
    )

    tokens: RefreshTokenOutput = container.refresh_user_token.execute(dto)

    return RefreshTokenResponse(
        access_token=tokens.token_pair.access_token.value,
        refresh_token=tokens.token_pair.refresh_token.value,
    )


@router.put("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email(
    request: ConfirmEmailRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: ConfirmEmailInput = ConfirmEmailInput(
        email=Email(request.email), code=request.code
    )

    await container.confirm_email.execute(dto)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user_id: UUID = Depends(get_current_user_id),
    container: RequestContainer = Depends(get_container),
):
    dto: DeleteUserInput = DeleteUserInput(user_id=current_user_id)

    await container.delete_user.execute(dto)


@router.post("/init-change-password", status_code=status.HTTP_200_OK)
async def init_change_password(
    request: InitiateChangePasswordRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: InitiateChangePasswordInput = InitiateChangePasswordInput(
        email=Email(request.email)
    )

    await container.initiate_change_password.execute(dto)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: ChangePasswordInput = ChangePasswordInput(
        Email(request.email),
        request.code,
        request.password,
    )

    await container.change_password.execute(dto)
