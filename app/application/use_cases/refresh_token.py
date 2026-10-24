from app.application.dtos.authentication import RefreshTokenInput
from app.application.dtos.tokens import TokenPair
from app.application.exceptions.token import InvalidToken
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.session_store import SessionStore
from app.application.ports.token_issuer import AccessTokenIssuer


class RefreshUserToken:
    """A new token pair for a refresh token, which stops working."""

    def __init__(
        self,
        sessions: SessionStore,
        access_tokens: AccessTokenIssuer,
        user_repo: UserRepo,
    ) -> None:
        self.sessions = sessions
        self.access_tokens = access_tokens
        self.user_repo = user_repo

    async def execute(self, dto: RefreshTokenInput) -> TokenPair:
        user_id, refresh_token = await self.sessions.rotate(dto.refresh_token)

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            await self.sessions.revoke_all(user_id)
            raise InvalidToken

        access = self.access_tokens.issue(user)
        return TokenPair(access.value, refresh_token, access.expires_in)
