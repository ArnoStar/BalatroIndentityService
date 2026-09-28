from typing import Protocol

from app.domain.value_object.email import Email


class ConfirmationCodeIssuer(Protocol):
    async def issue(self, email: Email) -> str: ...
    async def check(self, email: Email, code: str) -> bool: ...
