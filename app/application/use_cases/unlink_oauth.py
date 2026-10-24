from app.application.dtos.oauth import UnlinkOAuthAccountInput
from app.application.exceptions.oauth import LastSignInMethod, OAuthAccountDoesntExist
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.unit_of_work import UnitOfWork


class UnlinkOAuthAccount:
    def __init__(
        self,
        oauth_account_repo: OAuthAccountRepo,
        password_credential_repo: PasswordCredentialRepo,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.oauth_account_repo = oauth_account_repo
        self.password_credential_repo = password_credential_repo
        self.unit_of_work = unit_of_work

    async def execute(self, dto: UnlinkOAuthAccountInput) -> None:
        providers = await self.oauth_account_repo.get_providers(dto.user_id)

        if dto.provider not in providers:
            raise OAuthAccountDoesntExist

        has_password = (
            await self.password_credential_repo.get_by_user_id(dto.user_id) is not None
        )
        if not has_password and providers == {dto.provider}:
            raise LastSignInMethod

        await self.oauth_account_repo.delete_by_user_id(dto.provider, dto.user_id)
        await self.unit_of_work.commit()
