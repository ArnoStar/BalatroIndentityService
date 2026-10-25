from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions.user import UserAlreadyExist
from app.application.ports.repo.user_repo import UserRepo
from app.domain.entities.user import User
from app.domain.value_object.display_name import DisplayName
from app.domain.value_object.email import Email
from app.domain.value_object.role import Role
from app.infrastructure.sqlalchemy.model.user import UserModel
from app.infrastructure.sqlalchemy.model.user_role import UserRoleModel


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

    async def set_roles(
        self, user_id: UUID, roles: frozenset[Role], granted_by: UUID | None
    ) -> None:
        current = set(
            (
                await self.session.execute(
                    select(UserRoleModel.role).where(UserRoleModel.user_id == user_id)
                )
            ).scalars()
        )
        wanted = {r.value for r in roles}
        if current - wanted:
            await self.session.execute(
                delete(UserRoleModel).where(
                    UserRoleModel.user_id == user_id,
                    UserRoleModel.role.in_(current - wanted),
                )
            )
        if wanted - current:
            await self.session.execute(
                insert(UserRoleModel),
                [
                    {"user_id": user_id, "role": r, "granted_by": granted_by}
                    for r in sorted(wanted - current)
                ],
            )
        # the user loaded in this session reads its roles again
        model = await self.session.get(UserModel, user_id)
        if model is not None:
            await self.session.refresh(model, ["roles"])

    async def count_with_role(self, role: Role) -> int:
        result = await self.session.execute(
            select(func.count()).where(UserRoleModel.role == role.value)
        )
        return int(result.scalar_one())

    async def search(
        self, query: str | None, role: Role | None, limit: int, offset: int
    ) -> tuple[list[User], int]:
        where = []
        if query:
            pattern = f"%{query.lower()}%"
            where.append(
                or_(
                    func.lower(UserModel.email).like(pattern),
                    func.lower(UserModel.display_name).like(pattern),
                )
            )
        if role is not None:
            where.append(
                UserModel.id.in_(
                    select(UserRoleModel.user_id).where(
                        UserRoleModel.role == role.value
                    )
                )
            )
        total = (
            await self.session.execute(select(func.count(UserModel.id)).where(*where))
        ).scalar_one()
        models = (
            await self.session.execute(
                select(UserModel)
                .where(*where)
                .order_by(UserModel.created_at, UserModel.id)
                .limit(limit)
                .offset(offset)
            )
        ).scalars()
        return [self._to_entity(m) for m in models], int(total)

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
            # (a role removed from the code since is ignored)
            roles=frozenset(
                Role(r.role) for r in model.roles if r.role in Role._value2member_map_
            ),
        )
