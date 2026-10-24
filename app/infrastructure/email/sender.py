from typing import Protocol

from app.domain.value_object.email import Email


class EmailSender(Protocol):
    """Sends a plain text email (console, SMTP): what EmailCodeSender uses
    when this service sends its emails itself."""

    async def send(self, email: Email, subject: str, body: str) -> None:
        """Raises EmailDeliveryFailed."""
        ...
