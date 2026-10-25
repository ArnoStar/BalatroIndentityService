"""Errors as RFC 9457 problem details: ``{type, title, status, detail, code}``.
``code`` is stable; clients switch on it."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.application.exceptions.auth import (
    EmailNotVerified,
    InvalidConfirmationCode,
    InvalidEmailOrPassword,
    TooManyAttempts,
)
from app.application.exceptions.base import IdentityError
from app.application.exceptions.email import EmailDeliveryFailed
from app.application.exceptions.oauth import (
    InvalidOAuthState,
    LastSignInMethod,
    OAuthAccountConflict,
    OAuthAccountDoesntExist,
    OAuthAccountInUse,
    OAuthEmailNotVerified,
    OAuthExchangeFailed,
    OAuthProviderNotConfigured,
    RedirectUriNotAllowed,
)
from app.application.exceptions.roles import LastAdmin, NotAllowed
from app.application.exceptions.token import InvalidToken
from app.application.exceptions.user import UserAlreadyExist, UserDoesntExist
from app.domain.exceptions import DomainError

log = logging.getLogger(__name__)

STATUS: list[tuple[type[IdentityError], int]] = [
    (InvalidEmailOrPassword, 401),
    (InvalidToken, 401),
    (EmailNotVerified, 403),
    (OAuthEmailNotVerified, 403),
    (InvalidConfirmationCode, 400),
    (InvalidOAuthState, 400),
    (RedirectUriNotAllowed, 400),
    (OAuthExchangeFailed, 400),
    (OAuthProviderNotConfigured, 404),
    (OAuthAccountDoesntExist, 404),
    (UserDoesntExist, 404),
    (NotAllowed, 403),
    (LastAdmin, 409),
    (UserAlreadyExist, 409),
    (OAuthAccountConflict, 409),
    (OAuthAccountInUse, 409),
    (LastSignInMethod, 409),
    (TooManyAttempts, 429),
    (EmailDeliveryFailed, 503),
]


def problem(
    status: int,
    code: str,
    detail: str,
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    body = {
        "type": f"https://balatro-identity/errors/{code}",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code,
        **extra,
    }
    return JSONResponse(
        body,
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IdentityError)
    async def identity_error(_: Request, exc: IdentityError) -> JSONResponse:
        status = next((s for cls, s in STATUS if isinstance(exc, cls)), 400)
        headers: dict[str, str] = {}
        extra: dict[str, Any] = {}
        if isinstance(exc, InvalidToken):
            headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
        if isinstance(exc, TooManyAttempts):
            headers["Retry-After"] = str(exc.retry_after)
            extra["retry_after"] = exc.retry_after
        return problem(status, exc.code, exc.message, headers, **extra)

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return problem(422, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": list(e.get("loc", ())), "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]
        return problem(
            422,
            "invalid_request",
            "the request doesn't match the schema",
            errors=errors,
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        code = HTTPStatus(exc.status_code).phrase.lower().replace(" ", "_")
        return problem(exc.status_code, code, str(exc.detail), dict(exc.headers or {}))

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unexpected error", exc_info=exc)
        return problem(500, "internal_error", "unexpected server error")
