import json
from uuid import UUID

from redis.asyncio import Redis

from app.application.dtos.oauth import PendingOAuthLogin
from app.application.ports.oauth.oauth_state_store import OAuthStateStore
from app.domain.value_object.oauth_provider import OAuthProvider
from app.infrastructure.redis.redis import text


class RedisOAuthStateStore(OAuthStateStore):
    _PREFIX = "oauth_state:"
    TTL = 600  # 10 minutes to sign in at the provider

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def save(self, state: str, pending: PendingOAuthLogin) -> None:
        value = json.dumps(
            {
                "provider": pending.provider.value,
                "redirect_uri": pending.redirect_uri,
                "code_verifier": pending.code_verifier,
                "link_to": str(pending.link_to) if pending.link_to else None,
            }
        )
        await self.redis.set(f"{self._PREFIX}{state}", value, ex=self.TTL)

    async def pop(self, state: str) -> PendingOAuthLogin | None:
        value = await self.redis.getdel(f"{self._PREFIX}{state}")
        if value is None:
            return None

        data = json.loads(text(value))
        return PendingOAuthLogin(
            provider=OAuthProvider(data["provider"]),
            redirect_uri=data["redirect_uri"],
            code_verifier=data["code_verifier"],
            link_to=UUID(data["link_to"]) if data.get("link_to") else None,
        )
