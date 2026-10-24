from app.application.exceptions.base import IdentityError


class InvalidToken(IdentityError):
    code = "invalid_token"
    message = "the token is invalid or has expired"
