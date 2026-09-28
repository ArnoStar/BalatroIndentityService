from typing import Protocol
from uuid import UUID

from app.domain.entities.token_pair import TokenPair
from app.domain.value_object.tokens import AccessToken, RefreshToken


class TokenIssuer(Protocol):
    def issue(self, user_id: UUID) -> TokenPair: ...
    def refresh(self, token_pair: RefreshToken) -> TokenPair: ...
    def check(self, token: AccessToken) -> UUID: ...
