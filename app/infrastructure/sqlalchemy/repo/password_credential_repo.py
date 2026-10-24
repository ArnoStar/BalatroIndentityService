from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.domain.entities.password_credential import PasswordCredential
from app.domain.value_object.password import PasswordHash
from app.infrastructure.sqlalchemy.model.password_credential import (
    PasswordCredentialModel,
)


class SqlalchemyPasswordCredentialRepo(PasswordCredentialRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, password_credential: PasswordCredential) -> None:
        self.session.add(
            PasswordCredentialModel(
                user_id=password_credential.user_id,
                password_hash=password_credential.password_hash.value,
                created_at=password_credential.created_at,
                updated_at=password_credential.updated_at,
            )
        )
        await self.session.flush()

    async def get_by_user_id(self, user_id: UUID) -> PasswordCredential | None:
        model = await self.session.get(PasswordCredentialModel, user_id)
        if model is None:
            return None
        return PasswordCredential(
            user_id=model.user_id,
            password_hash=PasswordHash(model.password_hash),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def change_password(
        self,
        user_id: UUID,
        password_hash: PasswordHash,
    ) -> None:
        await self.session.execute(
            update(PasswordCredentialModel)
            .where(PasswordCredentialModel.user_id == user_id)
            .values(password_hash=password_hash.value)
        )

    async def delete_by_user_id(self, user_id: UUID) -> None:
        await self.session.execute(
            delete(PasswordCredentialModel).where(
                PasswordCredentialModel.user_id == user_id
            )
        )
