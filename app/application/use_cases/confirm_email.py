from datetime import UTC, datetime

from app.application.dtos.registration import ConfirmEmailInput
from app.application.exceptions.auth import InvalidConfirmationCode
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.unit_of_work import UnitOfWork


class ConfirmEmail:
    def __init__(
        self,
        confirmation_codes: ConfirmationCodes,
        user_repo: UserRepo,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.confirmation_codes = confirmation_codes
        self.user_repo = user_repo
        self.unit_of_work = unit_of_work

    async def execute(self, dto: ConfirmEmailInput) -> None:
        user = await self.user_repo.get_by_email(dto.email)

        valid = await self.confirmation_codes.check(
            CodePurpose.VERIFY_EMAIL, dto.email, dto.code
        )
        if not valid or user is None:
            raise InvalidConfirmationCode

        if not user.email_verified:
            await self.user_repo.verify_email(user.id, datetime.now(UTC))
            await self.unit_of_work.commit()
