from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.domain.entities.password_credential import PasswordCredential
from app.domain.value_object.password_hash import PasswordHash
from app.infrastructure.sqlalchemy.model.password_credential import (
    PasswordCredentialModel,
)


class SqlalchemyPasswordCredentialRepo(PasswordCredentialRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        password_credential: PasswordCredential,
    ) -> None:
        model = self._to_model(password_credential)

        self.session.add(model)

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> PasswordCredential | None:
        statement = select(PasswordCredentialModel).where(
            PasswordCredentialModel.user_id == user_id,
        )

        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def change_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> None:
        statement = (
            update(PasswordCredentialModel)
            .where(PasswordCredentialModel.user_id == user_id)
            .values(password_hash=password_hash)
        )

        await self.session.execute(statement)

    async def delete_by_id(
        self,
        user_id: UUID,
    ) -> None:
        statement = delete(PasswordCredentialModel).where(
            PasswordCredentialModel.user_id == user_id,
        )

        await self.session.execute(statement)

    @staticmethod
    def _to_model(
        password_credential: PasswordCredential,
    ) -> PasswordCredentialModel:
        return PasswordCredentialModel(
            user_id=password_credential.user_id,
            password_hash=password_credential.password_hash.value,
            created_at=password_credential.created_at,
            updated_at=password_credential.updated_at,
        )

    @staticmethod
    def _to_entity(
        model: PasswordCredentialModel,
    ) -> PasswordCredential:
        return PasswordCredential(
            user_id=model.user_id,
            password_hash=PasswordHash(model.password_hash),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
