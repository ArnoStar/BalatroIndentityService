from datetime import UTC, datetime
from uuid import uuid4

from app.application.dtos.registration import RegisterUserInput, RegisterUserOutput
from app.application.exceptions.auth import EmailNotVerified
from app.application.exceptions.user import UserAlreadyExist
from app.application.ports.confirmation_code_issuer import ConfirmationCodeIssuer
from app.application.ports.email_sender import EmailSender
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.password_credential import PasswordCredential
from app.domain.entities.user import User
from app.domain.value_object.password_hash import PasswordHash


class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        password_hasher: PasswordHasher,
        confirmation_code_issuer: ConfirmationCodeIssuer,
        email_sender: EmailSender,
    ) -> None:
        self.user_repo: UserRepo = user_repo
        self.password_credential_repo: PasswordCredentialRepo = password_credential_repo
        self.password_hasher: PasswordHasher = password_hasher
        self.confirmation_code_issuer: ConfirmationCodeIssuer = confirmation_code_issuer
        self.email_sender: EmailSender = email_sender

    async def execute(
        self,
        dto: RegisterUserInput,
    ) -> RegisterUserOutput:
        existing_user = await self.user_repo.get_by_email(dto.email)

        if existing_user is not None:
            if existing_user.email_verified_at is None:
                raise EmailNotVerified
            raise UserAlreadyExist

        now = datetime.now(UTC)
        user_id = uuid4()

        user = User(
            id=user_id,
            email=dto.email,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )

        password_hash = PasswordHash(
            self.password_hasher.hash(dto.password),
        )

        password_credential = PasswordCredential(
            user_id=user_id,
            password_hash=password_hash,
            created_at=now,
            updated_at=now,
        )

        await self.user_repo.create(user)
        await self.password_credential_repo.create(password_credential)

        confirmation_code = await self.confirmation_code_issuer.issue(user.email)

        await self.email_sender.send(
            user.email,
            "Confirm your email",
            f"This is your confirmation code: {confirmation_code}",
        )

        output: RegisterUserOutput = RegisterUserOutput(user_id=user.id)

        return output
