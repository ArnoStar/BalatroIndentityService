from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.oauth.oauth_account_issuer import OAuthAccountIssuer
from app.application.ports.oauth.oauth_state_manager import OAuthStateManager
from app.application.ports.oauth.oauth_url_manager import OAuthUrlManager
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.token_issuer import TokenIssuer
from app.application.use_cases.authenticate_oauth import AuthenticateOAuth
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.initiate_oauth import InitiateOAuth
from app.application.use_cases.refresh_token import RefreshUserToken
from app.application.use_cases.register_user import RegisterUser
from app.infrastructure.bcrypt import BcryptPasswordHasher
from app.infrastructure.config.settings import settings
from app.infrastructure.httpx.oauth_account_issuer import HttpxOAuthAccountIssuer
from app.infrastructure.pyjwt import PyJwtTokenIssuer
from app.infrastructure.redis.oauth_state_manager import RedisOAuthStateManager
from app.infrastructure.sqlalchemy.repo.oauth_account_repo import (
    SqlalchemyOAuthAccountRepo,
)
from app.infrastructure.sqlalchemy.repo.password_credential_repo import (
    SqlalchemyPasswordCredentialRepo,
)
from app.infrastructure.sqlalchemy.repo.user_repo import (
    SqlalchemyUserRepo,
)
from app.infrastructure.url_manager import UrlManager


class Container:
    def create_request_container(
        self,
        session: AsyncSession,
        httpx_client: AsyncClient,
    ) -> "RequestContainer":
        return RequestContainer(session, httpx_client)


class RequestContainer:
    def __init__(self, session: AsyncSession, httpx_client: AsyncClient) -> None:
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

        self.oauth_state_manager: OAuthStateManager = RedisOAuthStateManager()

        self.oauth_url_manager: OAuthUrlManager = UrlManager()

        self.oauth_account_issuer: OAuthAccountIssuer = HttpxOAuthAccountIssuer(
            httpx_client
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

        self.initiate_oauth: InitiateOAuth = InitiateOAuth(
            oauth_state_manager=self.oauth_state_manager,
            oauth_url_manager=self.oauth_url_manager,
        )

        self.authenticate_oauth: AuthenticateOAuth = AuthenticateOAuth(
            oauth_account_issuer=self.oauth_account_issuer,
            oauth_state_manager=self.oauth_state_manager,
            oauth_account_repo=self.oauth_account_repo,
            user_repo=self.user_repo,
            token_issuer=self.token_issuer,
        )
