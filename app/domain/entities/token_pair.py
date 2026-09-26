from dataclasses import dataclass

from app.domain.value_object.tokens import AccessToken, RefreshToken


@dataclass(frozen=True)
class TokenPair:
    access_token: AccessToken
    refresh_token: RefreshToken
