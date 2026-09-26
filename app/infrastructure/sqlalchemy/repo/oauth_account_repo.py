from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.domain.entities.oauth_account import OAuthAccount
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.sqlalchemy.model.oauth_account import OAuthAccountModel


class SqlalchemyOAuthAccountRepo(OAuthAccountRepo):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        account: OAuthAccount,
    ) -> None:
        model = self._to_model(account)

        self.session.add(model)

    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        statement = select(OAuthAccountModel).where(
            OAuthAccountModel.provider == provider.value,
            OAuthAccountModel.provider_user_id == provider_user_id,
        )

        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    @staticmethod
    def _to_model(
        account: OAuthAccount,
    ) -> OAuthAccountModel:
        return OAuthAccountModel(
            id=account.id,
            user_id=account.user_id,
            provider=account.provider.value,
            provider_user_id=account.provider_user_id,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    @staticmethod
    def _to_entity(
        model: OAuthAccountModel,
    ) -> OAuthAccount:
        return OAuthAccount(
            id=model.id,
            user_id=model.user_id,
            provider=OAuthProvider(model.provider),
            provider_user_id=model.provider_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
