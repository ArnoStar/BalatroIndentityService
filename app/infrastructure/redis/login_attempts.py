from redis.asyncio import Redis

from app.application.exceptions.auth import TooManyAttempts
from app.application.ports.login_attempts import LoginAttempts


class RedisLoginAttempts(LoginAttempts):
    """After 10 wrong passwords for an account, its logins are refused for
    the rest of a 15 minute window."""

    MAX_FAILURES = 10
    WINDOW = 15 * 60

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def check(self, key: str) -> None:
        failures = await self.redis.get(f"login_fail:{key}")
        if failures is not None and int(failures) >= self.MAX_FAILURES:
            retry_after = await self.redis.ttl(f"login_fail:{key}")
            raise TooManyAttempts(max(retry_after, 1))

    async def failed(self, key: str) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.incr(f"login_fail:{key}")
            pipe.expire(f"login_fail:{key}", self.WINDOW, nx=True)
            await pipe.execute()

    async def reset(self, key: str) -> None:
        await self.redis.delete(f"login_fail:{key}")
