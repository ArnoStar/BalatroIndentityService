from datetime import UTC, datetime

from app.application.dtos.authentication import ChangePasswordInput
from app.application.exceptions.auth import NoEmailWithThisCode
from app.application.exceptions.user import UserDoesntExist
from app.application.ports.confirmation_code_issuer import ConfirmationCodeIssuer
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import PasswordCredentialRepo
from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.password_credential import PasswordCredential
from app.domain.entities.user import User
from app.domain.value_object.password_hash import PasswordHash


class ChangePassword:
    def __init__(
        self,
        confirmation_code_issuer: ConfirmationCodeIssuer,
        password_hasher: PasswordHasher,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
    ) -> None:
        self.confirmation_code_issuer = confirmation_code_issuer
        self.password_hasher = password_hasher
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo

    async def execute(self, dto: ChangePasswordInput) -> None:
        is_confirmation_code_valid: bool = await self.confirmation_code_issuer.check(
            dto.email,
            dto.code,
        )

        if not is_confirmation_code_valid:
            raise NoEmailWithThisCode

        password_hash = self.password_hasher.hash(dto.password)

        user: User | None = await self.user_repo.get_by_email(dto.email)

        if user is None:
            raise UserDoesntExist

        now = datetime.now(UTC)

        if user.email_verified_at is None:
            await self.user_repo.verify_email(user.id, now)

        password_credential: (
            PasswordCredential | None
        ) = await self.password_credential_repo.get_by_user_id(user.id)

        if password_credential is None:
            await self.password_credential_repo.create(
                PasswordCredential(
                    user.id,
                    PasswordHash(password_hash),
                    now,
                    now,
                )
            )
        else:
            await self.password_credential_repo.change_password(user.id, password_hash)
