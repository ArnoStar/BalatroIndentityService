import secrets

from app.application.ports.oauth.oauth_state_manager import OAuthStateManager
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.redis.redis import redis


class RedisOAuthStateManager(OAuthStateManager):
    _PREFIX = "oauth:state:"
    _TTL = 600  # 10 minutes

    async def generate(self, provider: OAuthProvider) -> str:
        state = secrets.token_urlsafe(32)

        await redis.set(
            f"{self._PREFIX}{state}",
            provider.value,
            ex=self._TTL,
        )

        return state

    async def pop(self, state: str) -> OAuthProvider | None:
        key = f"{self._PREFIX}{state}"

        value = await redis.getdel(key)

        if value is None:
            return None

        return OAuthProvider(value.decode() if isinstance(value, bytes) else value)
