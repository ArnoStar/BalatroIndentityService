from app.application.dtos.authentication import AccountOutput, GetAccountInput
from app.application.exceptions.token import InvalidToken
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo


class GetAccount:
    def __init__(
        self,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        oauth_account_repo: OAuthAccountRepo,
    ) -> None:
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo
        self.oauth_account_repo = oauth_account_repo

    async def execute(self, dto: GetAccountInput) -> AccountOutput:
        user = await self.user_repo.get_by_id(dto.user_id)

        if user is None:  # deleted while its access token is still valid
            raise InvalidToken

        credential = await self.password_credential_repo.get_by_user_id(user.id)
        providers = await self.oauth_account_repo.get_providers(user.id)

        return AccountOutput(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            has_password=credential is not None,
            providers=sorted(providers),
            created_at=user.created_at,
            roles=sorted(user.roles),
        )
