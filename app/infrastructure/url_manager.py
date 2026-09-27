from app.application.ports.oauth.oauth_url_manager import OAuthUrlManager
from app.domain.value_object.oauth_provider import OAuthProvider


class UrlManager(OAuthUrlManager):
    def get_callback_url(
        self,
        provider: OAuthProvider,
    ) -> str:
        return f"/oauth/{provider.value}/callback"
