from datetime import UTC, datetime

from app.application.dtos.authentication import (
    RequestPasswordResetInput,
    ResetPasswordInput,
)
from app.application.exceptions.auth import InvalidConfirmationCode
from app.application.ports.code_sender import CodeSender
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.session_store import SessionStore
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases._shared import send_code
from app.domain.entities.password_credential import PasswordCredential


class RequestPasswordReset:
    """Emails a reset code to an existing account. Says nothing about whether
    the account exists."""

    def __init__(
        self,
        user_repo: UserRepo,
        confirmation_codes: ConfirmationCodes,
        code_sender: CodeSender,
    ) -> None:
        self.user_repo = user_repo
        self.confirmation_codes = confirmation_codes
        self.code_sender = code_sender

    async def execute(self, dto: RequestPasswordResetInput) -> None:
        user = await self.user_repo.get_by_email(dto.email)

        if user is None:
            return

        await send_code(
            self.confirmation_codes,
            self.code_sender,
            CodePurpose.RESET_PASSWORD,
            user.email,
        )


class ResetPassword:
    """Sets a new password with an emailed code. The code proves the user owns
    the address, so it also verifies it, and gives a password to an account
    that only signed in with a provider. Every session ends."""

    def __init__(
        self,
        confirmation_codes: ConfirmationCodes,
        password_hasher: PasswordHasher,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        unit_of_work: UnitOfWork,
        sessions: SessionStore,
    ) -> None:
        self.confirmation_codes = confirmation_codes
        self.password_hasher = password_hasher
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo
        self.unit_of_work = unit_of_work
        self.sessions = sessions

    async def execute(self, dto: ResetPasswordInput) -> None:
        user = await self.user_repo.get_by_email(dto.email)

        valid = await self.confirmation_codes.check(
            CodePurpose.RESET_PASSWORD, dto.email, dto.code
        )
        if not valid or user is None:
            raise InvalidConfirmationCode

        password_hash = await self.password_hasher.hash(dto.password.value)
        now = datetime.now(UTC)

        if not user.email_verified:
            await self.user_repo.verify_email(user.id, now)

        if await self.password_credential_repo.get_by_user_id(user.id) is None:
            await self.password_credential_repo.create(
                PasswordCredential(user.id, password_hash, now, now)
            )
        else:
            await self.password_credential_repo.change_password(user.id, password_hash)

        await self.unit_of_work.commit()
        await self.sessions.revoke_all(user.id)
