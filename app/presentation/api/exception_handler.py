from typing import TypeVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions.auth import (
    EmailNotVerified,
    InvalidEmailOrPassword,
    InvalidOAuthState,
    NoEmailWithThisCode,
)
from app.application.exceptions.deps import BelFlixException
from app.application.exceptions.oauth import OAuthAccountDoesntExist
from app.application.exceptions.password_credential import (
    PasswordCredentialAlreadyExist,
    PasswordCredentialDoesntExist,
)
from app.application.exceptions.token import InvalidToken, WrongTokenType
from app.application.exceptions.user import UserAlreadyExist, UserDoesntExist

ExceptionT = TypeVar("ExceptionT", bound=BelFlixException)


def register_exception_handlers(app: FastAPI) -> None:
    def add_exception_handler(
        exception: type[ExceptionT],
        status_code: int,
        detail: str,
    ) -> None:
        async def handler(
            request: Request,
            exc: ExceptionT,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=status_code,
                content={"detail": detail},
            )

        app.exception_handler(exception)(handler)

    add_exception_handler(
        InvalidEmailOrPassword,
        401,
        "Invalid email or password",
    )

    add_exception_handler(EmailNotVerified, 403, "You need to verify your email")

    add_exception_handler(
        PasswordCredentialAlreadyExist,
        409,
        "Credential already exists",
    )

    add_exception_handler(
        PasswordCredentialDoesntExist,
        404,
        "Credential wasn't found",
    )

    add_exception_handler(
        UserAlreadyExist,
        409,
        "User already exists",
    )

    add_exception_handler(
        UserDoesntExist,
        404,
        "User wasn't found",
    )

    add_exception_handler(InvalidOAuthState, 403, "Invalid OAuth state")

    add_exception_handler(
        OAuthAccountDoesntExist, 404, "This oauth account wasn't found"
    )

    add_exception_handler(
        NoEmailWithThisCode, 403, "No email with this confirmation code"
    )

    add_exception_handler(InvalidToken, 401, "Your token is invalid or has expired")

    add_exception_handler(WrongTokenType, 401, "Wrong token type")
