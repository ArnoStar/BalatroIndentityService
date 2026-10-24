from enum import StrEnum
from typing import Protocol

from app.domain.value_object.email import Email

# how long a code works (the stores expire it then; the emails say it)
CODE_LIFETIME_MINUTES = 10


class CodePurpose(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


class ConfirmationCodes(Protocol):
    """Short codes sent by email to prove that the user reads that inbox."""

    async def issue(self, purpose: CodePurpose, email: Email) -> str:
        """A new code (the previous one stops working). Raises TooManyAttempts
        when one was sent moments ago."""
        ...

    async def check(self, purpose: CodePurpose, email: Email, code: str) -> bool:
        """True once per code. After a few wrong guesses the code is dropped."""
        ...
