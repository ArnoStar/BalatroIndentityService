from datetime import UTC, datetime
from uuid import uuid4

from app.application.dtos.user import RegisterUserDTO
from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.user import User


class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepo,
    ) -> None:
        self.user_repo = user_repo

    async def execute(
        self,
        dto: RegisterUserDTO,
    ) -> User:
        existing_user = await self.user_repo.get_by_email(
            dto.email,
        )

        if existing_user is not None:
            raise ValueError("User with this email already exists")

        now = datetime.now(UTC)

        user = User(
            id=uuid4(),
            email=dto.email,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )

        await self.user_repo.create(user)

        return user
