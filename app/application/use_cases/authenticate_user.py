from app.application.dtos.authentication import (
    AuthUserInput,
    AuthUserOutput,
)
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.token_issuer import TokenIssuer


class AuthenticateUser:
    def __init__(
        self,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
    ) -> None:
        self.user_repo: UserRepo = user_repo
        self.password_credential_repo: PasswordCredentialRepo = password_credential_repo
        self.password_hasher: PasswordHasher = password_hasher
        self.token_issuer: TokenIssuer = token_issuer

    async def execute(
        self,
        input: AuthUserInput,
    ) -> AuthUserOutput:
        user = await self.user_repo.get_by_email(input.email)

        if user is None:
            raise ValueError("Invalid email or password")

        password_credential = await self.password_credential_repo.get_by_user_id(
            user.id
        )

        if password_credential is None:
            raise ValueError("Invalid email or password")

        password_valid = self.password_hasher.verify(
            input.password,
            password_credential.password_hash.value,
        )

        if not password_valid:
            raise ValueError("Invalid email or password")

        token_pair = self.token_issuer.issue(user.id)

        return AuthUserOutput(
            token_pair=token_pair,
        )
