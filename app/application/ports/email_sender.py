from typing import Protocol

from app.domain.value_object.email import Email


class EmailSender(Protocol):
    async def send(self, email: Email, subject: str, body: str) -> None:
        """Raises EmailDeliveryFailed."""
        ...
