from typing import Protocol

from app.application.ports.confirmation_codes import CodePurpose
from app.domain.value_object.email import Email


class CodeSender(Protocol):
    """Gets a confirmation code to the user's inbox: by email from here, or
    through the notification service (BalatroNotificationService)."""

    async def send_code(self, email: Email, purpose: CodePurpose, code: str) -> None:
        """Raises EmailDeliveryFailed when the code can't be handed over."""
        ...
