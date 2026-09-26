from datetime import UTC, datetime
from uuid import uuid4

from app.application.dtos.registration import RegisterUserInput, RegisterUserOutput
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
    ) -> None:
        self.user_repo: UserRepo = user_repo
        self.password_credential_repo: PasswordCredentialRepo = password_credential_repo
        self.password_hasher: PasswordHasher = password_hasher

    async def execute(
        self,
        dto: RegisterUserInput,
    ) -> RegisterUserOutput:
        existing_user = await self.user_repo.get_by_email(dto.email)

        if existing_user is not None:
            raise ValueError("User with this email already exists")

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

        output: RegisterUserOutput = RegisterUserOutput(user_id=user.id)

        return output


"""
application/
└── use_cases/
    ├── register_user.py
    ├── authenticate_user.py
    ├── authenticate_oauth.py
    ├── link_oauth_account.py
    ├── unlink_oauth_account.py
    ├── change_password.py
    └── verify_email.py
"""
