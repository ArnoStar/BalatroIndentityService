from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.token_issuer import TokenIssuer
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.refresh_token import RefreshUserToken
from app.application.use_cases.register_user import RegisterUser
from app.infrastructure.bcrypt import BcryptPasswordHasher
from app.infrastructure.config.settings import settings
from app.infrastructure.pyjwt import PyJwtTokenIssuer
from app.infrastructure.sqlalchemy.repo.oauth_account_repo import (
    SqlalchemyOAuthAccountRepo,
)
from app.infrastructure.sqlalchemy.repo.password_credential_repo import (
    SqlalchemyPasswordCredentialRepo,
)
from app.infrastructure.sqlalchemy.repo.user_repo import (
    SqlalchemyUserRepo,
)


class Container:
    def create_request_container(
        self,
        session: AsyncSession,
    ) -> "RequestContainer":
        return RequestContainer(session)


class RequestContainer:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

        # Repositories

        self.user_repo: UserRepo = SqlalchemyUserRepo(
            session=session,
        )

        self.password_credential_repo: PasswordCredentialRepo = (
            SqlalchemyPasswordCredentialRepo(
                session=session,
            )
        )

        self.oauth_account_repo: OAuthAccountRepo = SqlalchemyOAuthAccountRepo(
            session=session,
        )

        self.password_hasher: PasswordHasher = BcryptPasswordHasher()

        self.token_issuer: TokenIssuer = PyJwtTokenIssuer(
            settings.jwt_secret,
            settings.jwt_algorithm,
            timedelta(minutes=settings.access_jwt_lifetime_minutes),
            timedelta(days=settings.refresh_jwt_lifetime_days),
        )

        # Use cases

        self.register_user: RegisterUser = RegisterUser(
            user_repo=self.user_repo,
            password_credential_repo=self.password_credential_repo,
            password_hasher=self.password_hasher,
        )

        self.authenticate_user: AuthenticateUser = AuthenticateUser(
            user_repo=self.user_repo,
            password_credential_repo=self.password_credential_repo,
            password_hasher=self.password_hasher,
            token_issuer=self.token_issuer,
        )

        self.refresh_user_token: RefreshUserToken = RefreshUserToken(
            token_issuer=self.token_issuer
        )
