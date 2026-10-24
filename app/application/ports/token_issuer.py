from typing import Protocol
from uuid import UUID

from app.application.dtos.tokens import AccessToken
from app.domain.entities.user import User


class AccessTokenIssuer(Protocol):
    def issue(self, user: User) -> AccessToken: ...
    def verify(self, token: str) -> UUID:
        """The token's user. Raises InvalidToken."""
        ...
