from app.application.dtos.oauth import (
    InitiateOAuthInput,
    InitiateOAuthOutput,
)
from app.application.ports.oauth.oauth_state_manager import OAuthStateManager
from app.application.ports.oauth.oauth_url_manager import OAuthUrlManager


class InitiateOAuth:
    def __init__(
        self,
        oauth_state_manager: OAuthStateManager,
        oauth_url_manager: OAuthUrlManager,
    ) -> None:
        self.oauth_state_manager = oauth_state_manager
        self.oauth_url_manager = oauth_url_manager

    async def execute(
        self,
        dto: InitiateOAuthInput,
    ) -> InitiateOAuthOutput:
        state = await self.oauth_state_manager.generate(dto.provider)

        callback_url = self.oauth_url_manager.get_callback_url(
            dto.provider,
        )

        return InitiateOAuthOutput(
            state=state,
            callback_url=callback_url,
        )
