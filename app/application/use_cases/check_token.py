from uuid import UUID

from app.application.dtos.authentication import (
    CheckTokenInput,
    CheckTokenOutput,
)
from app.application.ports.token_issuer import TokenIssuer


class CheckUserToken:
    def __init__(self, token_issuer: TokenIssuer) -> None:
        self.token_issuer = token_issuer

    def execute(
        self,
        dto: CheckTokenInput,
    ) -> CheckTokenOutput:
        user_id: UUID = self.token_issuer.check(dto.access_token)

        return CheckTokenOutput(user_id=user_id)
