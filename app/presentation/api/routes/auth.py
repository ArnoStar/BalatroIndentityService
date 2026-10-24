from fastapi import APIRouter, Response, status

from app.application.dtos.authentication import (
    AuthUserInput,
    DeleteUserInput,
    GetAccountInput,
    LogoutAllInput,
    LogoutInput,
    RefreshTokenInput,
    RequestPasswordResetInput,
    ResetPasswordInput,
    UpdateAccountInput,
)
from app.application.dtos.registration import (
    ConfirmEmailInput,
    RegisterUserInput,
    ResendConfirmationInput,
)
from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.password import Password
from app.presentation.api.dependencies import AppContainer, CurrentUserId, Uses
from app.presentation.api.schemas.auth import (
    AccountResponse,
    ConfirmEmailRequest,
    EmailRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterUserRequest,
    RegisterUserResponse,
    ResetPasswordRequest,
    TokenResponse,
    UpdateAccountRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

NO_CONTENT = status.HTTP_204_NO_CONTENT
ACCEPTED = status.HTTP_202_ACCEPTED


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create an account (unverified until its email is confirmed)",
)
async def register_user(body: RegisterUserRequest, uses: Uses) -> RegisterUserResponse:
    """Emails a 6-digit code to confirm with ``POST /auth/confirm-email``.
    An existing unverified address answers 403 ``email_not_verified`` (ask for a
    new code with ``/auth/resend-confirmation``)."""
    output = await uses.register_user.execute(
        RegisterUserInput(
            email=Email(body.email),
            password=Password(body.password),
            display_name=DisplayName(body.display_name),
        )
    )
    return RegisterUserResponse(user_id=output.user_id)


@router.post("/confirm-email", status_code=NO_CONTENT, summary="Confirm an email")
async def confirm_email(body: ConfirmEmailRequest, uses: Uses) -> Response:
    await uses.confirm_email.execute(ConfirmEmailInput(Email(body.email), body.code))
    return Response(status_code=NO_CONTENT)


@router.post(
    "/resend-confirmation",
    status_code=ACCEPTED,
    summary="Send a new confirmation code",
)
async def resend_confirmation(body: EmailRequest, uses: Uses) -> Response:
    """Always 202, whether or not the account exists (429 when a code was
    sent less than a minute ago)."""
    await uses.resend_confirmation.execute(ResendConfirmationInput(Email(body.email)))
    return Response(status_code=ACCEPTED)


@router.post("/login", summary="Sign in with an email and a password")
async def login(body: LoginRequest, uses: Uses) -> TokenResponse:
    tokens = await uses.authenticate_user.execute(
        AuthUserInput(Email(body.email), body.password)
    )
    return TokenResponse.of(tokens)


@router.post("/refresh", summary="Exchange a refresh token for new tokens")
async def refresh(body: RefreshTokenRequest, uses: Uses) -> TokenResponse:
    """The refresh token is single use: keep the new one. Using an old one
    again ends its session (401 ``invalid_token``)."""
    tokens = await uses.refresh_user_token.execute(
        RefreshTokenInput(body.refresh_token)
    )
    return TokenResponse.of(tokens)


@router.post("/logout", status_code=NO_CONTENT, summary="End this session")
async def logout(body: RefreshTokenRequest, container: AppContainer) -> Response:
    await container.logout.execute(LogoutInput(body.refresh_token))
    return Response(status_code=NO_CONTENT)


@router.post("/logout-all", status_code=NO_CONTENT, summary="End every session")
async def logout_all(user_id: CurrentUserId, container: AppContainer) -> Response:
    await container.logout_all.execute(LogoutAllInput(user_id))
    return Response(status_code=NO_CONTENT)


@router.get("/me", summary="The signed-in account")
async def get_me(user_id: CurrentUserId, uses: Uses) -> AccountResponse:
    return AccountResponse.of(await uses.get_account.execute(GetAccountInput(user_id)))


@router.patch("/me", summary="Change the display name")
async def update_me(
    body: UpdateAccountRequest, user_id: CurrentUserId, uses: Uses
) -> AccountResponse:
    await uses.update_account.execute(
        UpdateAccountInput(
            user_id=user_id,
            display_name=(
                DisplayName(body.display_name)
                if body.display_name is not None
                else None
            ),
        )
    )
    return AccountResponse.of(await uses.get_account.execute(GetAccountInput(user_id)))


@router.delete("/me", status_code=NO_CONTENT, summary="Delete the account")
async def delete_me(user_id: CurrentUserId, uses: Uses) -> Response:
    await uses.delete_user.execute(DeleteUserInput(user_id))
    return Response(status_code=NO_CONTENT)


@router.post(
    "/password/forgot",
    status_code=ACCEPTED,
    summary="Email a password reset code",
)
async def forgot_password(body: EmailRequest, uses: Uses) -> Response:
    """Always 202, whether or not the account exists."""
    await uses.request_password_reset.execute(
        RequestPasswordResetInput(Email(body.email))
    )
    return Response(status_code=ACCEPTED)


@router.post(
    "/password/reset",
    status_code=NO_CONTENT,
    summary="Set a new password with the emailed code",
)
async def reset_password(body: ResetPasswordRequest, uses: Uses) -> Response:
    """Also verifies the email, and ends every session of the account."""
    await uses.reset_password.execute(
        ResetPasswordInput(Email(body.email), body.code, Password(body.password))
    )
    return Response(status_code=NO_CONTENT)
