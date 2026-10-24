from typing import Protocol

from app.domain.value_object.password import PasswordHash


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> PasswordHash: ...
    async def verify(self, password: str, password_hash: PasswordHash) -> bool: ...
    async def verify_dummy(self, password: str) -> None:
        """Takes as long as ``verify``: a login for an unknown email must not
        answer faster than one with a wrong password."""
        ...
