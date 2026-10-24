import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.application.exceptions.email import EmailDeliveryFailed
from app.application.ports.email_sender import EmailSender
from app.domain.value_object.email import Email

log = logging.getLogger(__name__)


class SmtpEmailSender(EmailSender):
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        security: str = "starttls",
        timeout: float = 15,
    ) -> None:
        if security not in ("starttls", "ssl", "none"):
            raise ValueError("SMTP_SECURITY is starttls, ssl or none")
        self.host = host
        self.port = port
        self.sender = sender
        self.username = username
        self.password = password
        self.security = security
        self.timeout = timeout

    async def send(self, email: Email, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = email.value
        message["Subject"] = subject
        message.set_content(body)
        try:
            await asyncio.to_thread(self._send, message)
        except (OSError, smtplib.SMTPException) as exc:
            log.exception("SMTP delivery to %s failed", email.value)
            raise EmailDeliveryFailed from exc

    def _send(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()
        smtp: smtplib.SMTP
        if self.security == "ssl":
            smtp = smtplib.SMTP_SSL(
                self.host, self.port, timeout=self.timeout, context=context
            )
        else:
            smtp = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        with smtp:
            if self.security == "starttls":
                smtp.starttls(context=context)
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)
