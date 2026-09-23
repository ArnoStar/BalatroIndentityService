from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.user import User
from app.domain.value_object.email import Email
from app.infrastructure.sqlalchemy.model.user import UserModel


class SqlalchemyUserRepo(UserRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> None:
        model = self._to_model(user)

        self.session.add(model)

    async def get_by_id(self, id: UUID) -> User | None:
        statement = select(UserModel).where(UserModel.id == id)

        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_email(self, email: Email) -> User | None:
        statement = select(UserModel).where(UserModel.email == email.value)

        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def delete_by_id(self, id: UUID) -> None:
        statement = delete(UserModel).where(UserModel.id == id)

        await self.session.execute(statement)

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email.value,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            email_verified_at=model.email_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
