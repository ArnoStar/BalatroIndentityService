from app.application.dtos.oauth import UnlinkOAuthAccountInput
from app.application.exceptions.oauth import OAuthAccountDoesntExist
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo


class UnlinkOAuthAccount:
    def __init__(
        self,
        oauth_account_repo: OAuthAccountRepo,
    ) -> None:
        self.oauth_account_repo = oauth_account_repo

    async def execute(
        self,
        dto: UnlinkOAuthAccountInput,
    ) -> None:
        account = await self.oauth_account_repo.delete_by_user_id(
            provider=dto.provider,
            user_id=dto.user_id,
        )

        if account is None:
            raise OAuthAccountDoesntExist
