from app.application.dtos.authentication import InitiateChangePasswordInput
from app.application.ports.confirmation_code_issuer import ConfirmationCodeIssuer
from app.application.ports.email_sender import EmailSender


class InitiateChangePassword:
    def __init__(
        self,
        confirmation_code_issuer: ConfirmationCodeIssuer,
        email_sender: EmailSender,
    ) -> None:
        self.confirmation_code_issuer = confirmation_code_issuer
        self.email_sender = email_sender

    async def execute(self, dto: InitiateChangePasswordInput) -> None:
        confirmation_code: str = await self.confirmation_code_issuer.issue(dto.email)

        await self.email_sender.send(
            dto.email,
            "Your confirmation code for password change",
            f"Your confirmation code is: {confirmation_code}",
        )
