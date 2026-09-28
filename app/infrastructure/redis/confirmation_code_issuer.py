import secrets

from app.application.ports.confirmation_code_issuer import ConfirmationCodeIssuer
from app.domain.value_object.email import Email
from app.infrastructure.redis.redis import redis


class RedisConfirmationCodeIssuer(ConfirmationCodeIssuer):
    _PREFIX = "confirmation:code:"
    _TTL = 600  # 10 minutes

    async def issue(self, email: Email) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"

        await redis.set(
            f"{self._PREFIX}{email.value}",
            code,
            ex=self._TTL,
        )

        return code

    async def check(
        self,
        email: Email,
        code: str,
    ) -> bool:
        stored_code = await redis.get(
            f"{self._PREFIX}{email.value}",
        )

        if stored_code is None:
            return False

        if isinstance(stored_code, bytes):
            stored_code = stored_code.decode("utf-8")

        if secrets.compare_digest(stored_code, code):
            await redis.delete(
                f"{self._PREFIX}{email.value}",
            )
            return True
        return False
