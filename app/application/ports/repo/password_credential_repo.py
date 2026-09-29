from typing import Protocol
from uuid import UUID

from app.domain.entities.password_credential import PasswordCredential


class PasswordCredentialRepo(Protocol):
    async def create(self, password_credential: PasswordCredential) -> None: ...
    async def get_by_user_id(self, user_id: UUID) -> PasswordCredential | None: ...
    async def change_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> None: ...
    async def delete_by_id(self, user_id: UUID) -> None: ...
