from typing import Protocol


class UnitOfWork(Protocol):
    """The repositories' changes are stored together by ``commit``. A use case
    commits before it answers, so a client never acts on unsaved changes."""

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
