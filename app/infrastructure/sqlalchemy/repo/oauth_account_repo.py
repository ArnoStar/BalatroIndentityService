from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.domain.entities.oauth_account import OAuthAccount
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.sqlalchemy.model.oauth_account import OAuthAccountModel


class SqlalchemyOAuthAccountRepo(OAuthAccountRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, account: OAuthAccount) -> None:
        self.session.add(
            OAuthAccountModel(
                id=account.id,
                user_id=account.user_id,
                provider=account.provider.value,
                provider_user_id=account.provider_user_id,
                created_at=account.created_at,
                updated_at=account.updated_at,
            )
        )
        await self.session.flush()

    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        result = await self.session.execute(
            select(OAuthAccountModel).where(
                OAuthAccountModel.provider == provider.value,
                OAuthAccountModel.provider_user_id == provider_user_id,
            )
        )
        model = result.scalar_one_or_none()
        return None if model is None else self._to_entity(model)

    async def get_by_user_id(
        self,
        provider: OAuthProvider,
        user_id: UUID,
    ) -> OAuthAccount | None:
        result = await self.session.execute(
            select(OAuthAccountModel).where(
                OAuthAccountModel.provider == provider.value,
                OAuthAccountModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return None if model is None else self._to_entity(model)

    async def get_providers(self, user_id: UUID) -> set[OAuthProvider]:
        result = await self.session.execute(
            select(OAuthAccountModel.provider).where(
                OAuthAccountModel.user_id == user_id
            )
        )
        return {OAuthProvider(provider) for provider in result.scalars()}

    async def delete_by_user_id(
        self,
        provider: OAuthProvider,
        user_id: UUID,
    ) -> bool:
        result = await self.session.execute(
            delete(OAuthAccountModel)
            .where(
                OAuthAccountModel.provider == provider.value,
                OAuthAccountModel.user_id == user_id,
            )
            .returning(OAuthAccountModel.id)
        )
        return result.first() is not None

    @staticmethod
    def _to_entity(model: OAuthAccountModel) -> OAuthAccount:
        return OAuthAccount(
            id=model.id,
            user_id=model.user_id,
            provider=OAuthProvider(model.provider),
            provider_user_id=model.provider_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
