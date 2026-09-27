from datetime import UTC, datetime
from uuid import uuid4

from app.application.dtos.oauth import (
    AuthenticateOAuthInput,
    AuthenticateOAuthOutput,
)
from app.application.exceptions.auth import InvalidOAuthState
from app.application.ports.oauth.oauth_account_issuer import OAuthAccountIssuer
from app.application.ports.oauth.oauth_state_manager import OAuthStateManager
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.token_issuer import TokenIssuer
from app.domain.entities.oauth_account import OAuthAccount
from app.domain.entities.user import User


class AuthenticateOAuth:
    def __init__(
        self,
        oauth_account_issuer: OAuthAccountIssuer,
        oauth_state_manager: OAuthStateManager,
        oauth_account_repo: OAuthAccountRepo,
        user_repo: UserRepo,
        token_issuer: TokenIssuer,
    ) -> None:
        self.oauth_account_issuer = oauth_account_issuer
        self.oauth_state_manager = oauth_state_manager
        self.oauth_account_repo = oauth_account_repo
        self.user_repo = user_repo
        self.token_issuer = token_issuer

    async def execute(
        self,
        dto: AuthenticateOAuthInput,
    ) -> AuthenticateOAuthOutput:
        stored_provider = await self.oauth_state_manager.pop(dto.state)

        if stored_provider is None:
            raise InvalidOAuthState

        if stored_provider != dto.provider:
            raise InvalidOAuthState

        identity = await self.oauth_account_issuer.issue(
            provider=dto.provider,
            code=dto.code,
        )

        oauth_account = await self.oauth_account_repo.get_by_provider(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        )

        if oauth_account is not None:
            token_pair = self.token_issuer.issue(oauth_account.user_id)

            return AuthenticateOAuthOutput(
                token_pair=token_pair,
            )

        user = await self.user_repo.get_by_email(identity.email)

        now = datetime.now(UTC)

        if user is None:
            user = User(
                id=uuid4(),
                email=identity.email,
                email_verified_at=now,
                created_at=now,
                updated_at=now,
            )

            await self.user_repo.create(user)

        oauth_account = OAuthAccount(
            id=uuid4(),
            user_id=user.id,
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
            created_at=now,
            updated_at=now,
        )

        await self.oauth_account_repo.create(oauth_account)

        token_pair = self.token_issuer.issue(user.id)

        return AuthenticateOAuthOutput(
            token_pair=token_pair,
        )
