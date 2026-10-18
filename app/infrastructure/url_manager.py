from app.application.exceptions.oauth import RedirectUriNotSet
from app.application.ports.oauth.oauth_url_manager import OAuthUrlManager
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.config.settings import settings


class UrlManager(OAuthUrlManager):
    def get_callback_url(
        self,
        provider: OAuthProvider,
    ) -> str:
        if settings.google_redirect_uri is None:
            raise RedirectUriNotSet
        return settings.google_redirect_uri
