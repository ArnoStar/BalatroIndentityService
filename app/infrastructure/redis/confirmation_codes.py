import secrets

from redis.asyncio import Redis

from app.application.exceptions.auth import TooManyAttempts
from app.application.ports.confirmation_codes import CodePurpose, ConfirmationCodes
from app.domain.value_object.email import Email
from app.infrastructure.redis.redis import text


class RedisConfirmationCodes(ConfirmationCodes):
    """Six-digit codes, valid for 10 minutes and 5 guesses, at most one sent
    a minute per address and purpose."""

    TTL = 600
    MAX_ATTEMPTS = 5
    COOLDOWN = 60

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @staticmethod
    def _key(purpose: CodePurpose, email: Email) -> str:
        return f"code:{purpose}:{email.value}"

    async def issue(self, purpose: CodePurpose, email: Email) -> str:
        cooldown_key = f"code_sent:{purpose}:{email.value}"
        if not await self.redis.set(cooldown_key, "1", ex=self.COOLDOWN, nx=True):
            retry_after = await self.redis.ttl(cooldown_key)
            raise TooManyAttempts(
                max(retry_after, 1), "a code was just sent, wait a minute"
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        key = self._key(purpose, email)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(key)
            pipe.hset(key, mapping={"code": code, "attempts": 0})
            pipe.expire(key, self.TTL)
            await pipe.execute()

        return code

    async def check(self, purpose: CodePurpose, email: Email, code: str) -> bool:
        key = self._key(purpose, email)
        stored = await self.redis.hget(key, "code")
        if stored is None:
            return False

        attempts = await self.redis.hincrby(key, "attempts", 1)
        if attempts > self.MAX_ATTEMPTS:
            await self.redis.delete(key)
            return False

        if not secrets.compare_digest(text(stored), code.strip()):
            return False

        # only one of two simultaneous checks deletes it
        return bool(await self.redis.delete(key))
