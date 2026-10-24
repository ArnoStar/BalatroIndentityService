from typing import Protocol
from uuid import UUID

from app.domain.entities.password_credential import PasswordCredential
from app.domain.value_object.password import PasswordHash


class PasswordCredentialRepo(Protocol):
    async def create(self, password_credential: PasswordCredential) -> None: ...
    async def get_by_user_id(self, user_id: UUID) -> PasswordCredential | None: ...
    async def change_password(
        self,
        user_id: UUID,
        password_hash: PasswordHash,
    ) -> None: ...
    async def delete_by_user_id(self, user_id: UUID) -> None: ...
