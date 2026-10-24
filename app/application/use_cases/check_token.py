from app.application.dtos.authentication import CheckTokenInput, CheckTokenOutput
from app.application.ports.token_issuer import AccessTokenIssuer


class CheckUserToken:
    def __init__(self, access_tokens: AccessTokenIssuer) -> None:
        self.access_tokens = access_tokens

    def execute(self, dto: CheckTokenInput) -> CheckTokenOutput:
        return CheckTokenOutput(user_id=self.access_tokens.verify(dto.access_token))
