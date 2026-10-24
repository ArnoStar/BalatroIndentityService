from app.application.dtos.registration import ResendConfirmationInput
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.application.ports.email_sender import EmailSender
from app.application.ports.repo.user_repo import UserRepo
from app.application.use_cases._shared import send_code


class ResendConfirmation:
    """Sends a new confirmation code to an unverified account. Says nothing
    about whether the account exists."""

    def __init__(
        self,
        user_repo: UserRepo,
        confirmation_codes: ConfirmationCodes,
        email_sender: EmailSender,
    ) -> None:
        self.user_repo = user_repo
        self.confirmation_codes = confirmation_codes
        self.email_sender = email_sender

    async def execute(self, dto: ResendConfirmationInput) -> None:
        user = await self.user_repo.get_by_email(dto.email)

        if user is None or user.email_verified:
            return

        await send_code(
            self.confirmation_codes,
            self.email_sender,
            CodePurpose.VERIFY_EMAIL,
            user.email,
        )
