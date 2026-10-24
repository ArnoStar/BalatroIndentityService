import asyncio

import bcrypt

from app.application.ports.password_hasher import PasswordHasher
from app.domain.value_object.password import PasswordHash

# bcrypt reads at most 72 bytes; longer passwords (only possible at login,
# new ones are checked) are cut rather than refused
_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BYTES]


class BcryptPasswordHasher(PasswordHasher):
    """bcrypt, in a worker thread: a hash takes about 0.2 s of CPU, which
    must not stall the event loop."""

    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds
        self._dummy = bcrypt.hashpw(b"dummy password", bcrypt.gensalt(rounds))

    async def hash(self, password: str) -> PasswordHash:
        hashed = await asyncio.to_thread(
            bcrypt.hashpw, _encode(password), bcrypt.gensalt(self.rounds)
        )
        return PasswordHash(hashed.decode("utf-8"))

    async def verify(self, password: str, password_hash: PasswordHash) -> bool:
        return await asyncio.to_thread(
            bcrypt.checkpw, _encode(password), password_hash.value.encode("utf-8")
        )

    async def verify_dummy(self, password: str) -> None:
        await asyncio.to_thread(bcrypt.checkpw, _encode(password), self._dummy)
