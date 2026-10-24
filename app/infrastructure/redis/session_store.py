import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import WatchError

from app.application.exceptions.token import InvalidToken
from app.application.ports.session_store import SessionStore
from app.infrastructure.redis.redis import text


def _digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class RedisSessionStore(SessionStore):
    """A refresh token is ``<session id>.<secret>``. Redis keeps, per session,
    its user and the hash of its current secret (``session:<id>``), and per
    user the ids of their sessions (``user_sessions:<user id>``). Both expire
    with the refresh token; each refresh pushes the expiry back."""

    _SESSION = "session:"
    _USER = "user_sessions:"

    def __init__(self, redis: Redis, lifetime: timedelta) -> None:
        self.redis = redis
        self.ttl = int(lifetime.total_seconds())

    async def create(self, user_id: UUID) -> str:
        session_id = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(32)
        user_key = f"{self._USER}{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(
                f"{self._SESSION}{session_id}",
                mapping={"user_id": str(user_id), "secret": _digest(secret)},
            )
            pipe.expire(f"{self._SESSION}{session_id}", self.ttl)
            pipe.sadd(user_key, session_id)
            pipe.expire(user_key, self.ttl)
            await pipe.execute()

        return f"{session_id}.{secret}"

    async def rotate(self, refresh_token: str) -> tuple[UUID, str]:
        session_id, _, secret = refresh_token.partition(".")
        if not session_id or not secret:
            raise InvalidToken
        key = f"{self._SESSION}{session_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(key)
                session = {
                    text(k): text(v) for k, v in (await pipe.hgetall(key)).items()
                }
                if not session:
                    raise InvalidToken

                user_id = UUID(session["user_id"])
                if not secrets.compare_digest(session["secret"], _digest(secret)):
                    # an old token again: it was copied, so the session ends
                    pipe.multi()  # type: ignore[no-untyped-call]
                    pipe.delete(key)
                    pipe.srem(f"{self._USER}{user_id}", session_id)
                    await pipe.execute()
                    raise InvalidToken

                new_secret = secrets.token_urlsafe(32)
                pipe.multi()  # type: ignore[no-untyped-call]
                pipe.hset(key, "secret", _digest(new_secret))
                pipe.expire(key, self.ttl)
                pipe.expire(f"{self._USER}{user_id}", self.ttl)
                await pipe.execute()
            except WatchError as exc:  # refreshed at the same moment elsewhere
                raise InvalidToken from exc

        return user_id, f"{session_id}.{new_secret}"

    async def revoke(self, refresh_token: str) -> None:
        session_id, _, secret = refresh_token.partition(".")
        key = f"{self._SESSION}{session_id}"
        reply = await self.redis.hgetall(key) if session_id else {}
        session = {text(k): text(v) for k, v in reply.items()}

        if session and secrets.compare_digest(session["secret"], _digest(secret)):
            await self.redis.delete(key)
            await self.redis.srem(f"{self._USER}{session['user_id']}", session_id)

    async def revoke_all(self, user_id: UUID) -> None:
        user_key = f"{self._USER}{user_id}"
        session_ids = await self.redis.smembers(user_key)
        keys = [f"{self._SESSION}{text(sid)}" for sid in session_ids]
        await self.redis.delete(user_key, *keys)
