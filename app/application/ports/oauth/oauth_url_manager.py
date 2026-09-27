from typing import Protocol

from app.domain.value_object.oauth_provider import OAuthProvider


class OAuthUrlManager(Protocol):
    def get_callback_url(self, provider: OAuthProvider) -> str: ...
