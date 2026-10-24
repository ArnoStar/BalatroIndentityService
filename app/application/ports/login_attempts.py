from typing import Protocol


class LoginAttempts(Protocol):
    """Slows down password guessing on one account."""

    async def check(self, key: str) -> None:
        """Raises TooManyAttempts while ``key`` is locked out."""
        ...

    async def failed(self, key: str) -> None: ...
    async def reset(self, key: str) -> None: ...
