from app.application.dtos.authentication import AuthUserInput
from app.application.dtos.tokens import TokenPair
from app.application.exceptions.auth import EmailNotVerified, InvalidEmailOrPassword
from app.application.ports.login_attempts import LoginAttempts
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.session_store import SessionStore
from app.application.ports.token_issuer import AccessTokenIssuer
from app.application.use_cases._shared import issue_tokens


class AuthenticateUser:
    """Signs in with an email and a password."""

    def __init__(
        self,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        password_hasher: PasswordHasher,
        login_attempts: LoginAttempts,
        access_tokens: AccessTokenIssuer,
        sessions: SessionStore,
    ) -> None:
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo
        self.password_hasher = password_hasher
        self.login_attempts = login_attempts
        self.access_tokens = access_tokens
        self.sessions = sessions

    async def execute(self, dto: AuthUserInput) -> TokenPair:
        key = dto.email.value
        await self.login_attempts.check(key)

        user = await self.user_repo.get_by_email(dto.email)
        credential = (
            await self.password_credential_repo.get_by_user_id(user.id)
            if user is not None
            else None
        )

        if user is None or credential is None:
            await self.password_hasher.verify_dummy(dto.password)
            await self.login_attempts.failed(key)
            raise InvalidEmailOrPassword

        if not await self.password_hasher.verify(
            dto.password, credential.password_hash
        ):
            await self.login_attempts.failed(key)
            raise InvalidEmailOrPassword

        await self.login_attempts.reset(key)

        # (checked after the password: only the owner learns it's unverified)
        if not user.email_verified:
            raise EmailNotVerified

        return await issue_tokens(self.access_tokens, self.sessions, user)
