from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions.user import UserAlreadyExist
from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.user import User
from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.infrastructure.sqlalchemy.model.user import UserModel


class SqlalchemyUserRepo(UserRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> None:
        self.session.add(self._to_model(user))
        try:
            await self.session.flush()
        except IntegrityError as exc:  # registered at the same moment
            await self.session.rollback()
            raise UserAlreadyExist from exc

    async def get_by_id(self, id: UUID) -> User | None:
        model = await self.session.get(UserModel, id)
        return None if model is None else self._to_entity(model)

    async def get_by_email(self, email: Email) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.value)
        )
        model = result.scalar_one_or_none()
        return None if model is None else self._to_entity(model)

    async def verify_email(self, user_id: UUID, verified_at: datetime) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(email_verified_at=verified_at)
        )

    async def set_display_name(self, user_id: UUID, display_name: DisplayName) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(display_name=display_name.value)
        )

    async def delete_by_id(self, id: UUID) -> None:
        # the database deletes the user's credential and accounts (ON DELETE CASCADE)
        await self.session.execute(delete(UserModel).where(UserModel.id == id))

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email.value,
            display_name=user.display_name.value,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            display_name=DisplayName(model.display_name),
            email_verified_at=model.email_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
