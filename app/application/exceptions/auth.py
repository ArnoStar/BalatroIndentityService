from app.application.exceptions.base import IdentityError


class InvalidEmailOrPassword(IdentityError):
    code = "invalid_credentials"
    message = "invalid email or password"


class EmailNotVerified(IdentityError):
    code = "email_not_verified"
    message = "the email address is not verified yet"


class InvalidConfirmationCode(IdentityError):
    code = "invalid_code"
    message = "the code is wrong or has expired"


class TooManyAttempts(IdentityError):
    code = "too_many_attempts"
    message = "too many attempts, try again later"

    def __init__(self, retry_after: int, message: str | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
