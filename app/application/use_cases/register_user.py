from datetime import UTC, datetime
from uuid import uuid4

from app.application.dtos.registration import RegisterUserInput, RegisterUserOutput
from app.application.exceptions.auth import EmailNotVerified
from app.application.exceptions.user import UserAlreadyExist
from app.application.ports.code_sender import CodeSender
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases._shared import try_send_code
from app.domain.entities.password_credential import PasswordCredential
from app.domain.entities.user import User


class RegisterUser:
    """Creates an unverified account and emails it a confirmation code. The
    account can sign in once the code is confirmed (ConfirmEmail)."""

    def __init__(
        self,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        password_hasher: PasswordHasher,
        unit_of_work: UnitOfWork,
        confirmation_codes: ConfirmationCodes,
        code_sender: CodeSender,
    ) -> None:
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo
        self.password_hasher = password_hasher
        self.unit_of_work = unit_of_work
        self.confirmation_codes = confirmation_codes
        self.code_sender = code_sender

    async def execute(self, dto: RegisterUserInput) -> RegisterUserOutput:
        existing_user = await self.user_repo.get_by_email(dto.email)

        if existing_user is not None:
            # (ResendConfirmation sends a new code; a squatted address is
            # taken back with the password reset, which also verifies it)
            if not existing_user.email_verified:
                raise EmailNotVerified
            raise UserAlreadyExist

        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            email=dto.email,
            display_name=dto.display_name,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )
        password_hash = await self.password_hasher.hash(dto.password.value)

        await self.user_repo.create(user)
        await self.password_credential_repo.create(
            PasswordCredential(
                user_id=user.id,
                password_hash=password_hash,
                created_at=now,
                updated_at=now,
            )
        )
        await self.unit_of_work.commit()

        await try_send_code(
            self.confirmation_codes,
            self.code_sender,
            CodePurpose.VERIFY_EMAIL,
            user.email,
        )

        return RegisterUserOutput(user_id=user.id)
