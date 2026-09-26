from app.application.dtos.authentication import (
    RefreshTokenInput,
    RefreshTokenOutput,
)
from app.application.ports.token_issuer import TokenIssuer


class RefreshUserToken:
    def __init__(self, token_issuer: TokenIssuer) -> None:
        self.token_issuer = token_issuer

    def execute(
        self,
        dto: RefreshTokenInput,
    ) -> RefreshTokenOutput:
        token_pair = self.token_issuer.refresh(dto.refresh_token)

        return RefreshTokenOutput(
            token_pair=token_pair,
        )
