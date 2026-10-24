from app.application.ports.code_sender import CodeSender
from app.application.ports.confirmation_codes import CODE_LIFETIME_MINUTES, CodePurpose
from app.domain.value_object.email import Email
from app.infrastructure.email.sender import EmailSender

_MESSAGES = {
    CodePurpose.VERIFY_EMAIL: (
        "Confirm your email",
        "Your confirmation code is {code}. It expires in {minutes} minutes.",
    ),
    CodePurpose.RESET_PASSWORD: (
        "Reset your password",
        (
            "Your password reset code is {code}. It expires in {minutes} minutes.\n"
            "If you didn't ask for it, ignore this email."
        ),
    ),
}


class EmailCodeSender(CodeSender):
    """The code in a plain email sent from here (console or SMTP): for this
    service alone. With the notification service, NotificationServiceCodeSender
    hands the code over instead, and that service writes the email."""

    def __init__(self, email_sender: EmailSender) -> None:
        self.email_sender = email_sender

    async def send_code(self, email: Email, purpose: CodePurpose, code: str) -> None:
        subject, body = _MESSAGES[purpose]
        await self.email_sender.send(
            email, subject, body.format(code=code, minutes=CODE_LIFETIME_MINUTES)
        )
