from datetime import UTC, datetime

from app.application.dtos.registration import ConfirmEmailInput
from app.application.exceptions.auth import NoEmailWithThisCode
from app.application.ports.confirmation_code_issuer import ConfirmationCodeIssuer
from app.application.ports.repo.user_repo import UserRepo


class ConfirmEmail:
    def __init__(
        self,
        confirmation_code_issuer: ConfirmationCodeIssuer,
        user_repo: UserRepo,
    ) -> None:
        self.confirmation_code_issuer = confirmation_code_issuer
        self.user_repo = user_repo

    async def execute(
        self,
        dto: ConfirmEmailInput,
    ) -> None:
        is_valid = await self.confirmation_code_issuer.check(
            dto.email,
            dto.code,
        )

        if not is_valid:
            raise NoEmailWithThisCode

        user = await self.user_repo.get_by_email(dto.email)

        if user is None:
            raise NoEmailWithThisCode

        await self.user_repo.verify_email(
            user_id=user.id,
            verified_at=datetime.now(UTC),
        )
