import logging

from app.application.ports.email_sender import EmailSender
from app.domain.value_object.email import Email

log = logging.getLogger("identity.email")


class ConsoleEmailSender(EmailSender):
    """Development: the email goes to the log (codes included)."""

    async def send(self, email: Email, subject: str, body: str) -> None:
        log.warning("email to %s: %s\n%s", email.value, subject, body)
