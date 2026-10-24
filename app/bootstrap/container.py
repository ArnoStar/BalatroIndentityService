"""The composition root: the only place that knows every layer. ``Container``
holds what lives as long as the process (connections, the signing key);
``RequestContainer`` builds the use cases of one request on its database
session."""

from datetime import timedelta

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.ports.code_sender import CodeSender
from app.application.ports.oauth.oauth_client import OAuthClient
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_issuer import AccessTokenIssuer
from app.application.use_cases.authenticate_oauth import AuthenticateOAuth
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.check_token import CheckUserToken
from app.application.use_cases.confirm_email import ConfirmEmail
from app.application.use_cases.delete_user import DeleteUser
from app.application.use_cases.get_account import GetAccount
from app.application.use_cases.initiate_oauth import InitiateOAuth, ListOAuthProviders
from app.application.use_cases.logout import Logout, LogoutAll
from app.application.use_cases.password_reset import (
    RequestPasswordReset,
    ResetPassword,
)
from app.application.use_cases.refresh_token import RefreshUserToken
from app.application.use_cases.register_user import RegisterUser
from app.application.use_cases.resend_confirmation import ResendConfirmation
from app.application.use_cases.unlink_oauth import UnlinkOAuthAccount
from app.application.use_cases.update_account import UpdateAccount
from app.infrastructure.bcrypt import BcryptPasswordHasher
from app.infrastructure.config.settings import EmailBackend, Settings
from app.infrastructure.email.code_sender import EmailCodeSender
from app.infrastructure.email.console import ConsoleEmailSender
from app.infrastructure.email.sender import EmailSender
from app.infrastructure.email.smtp import SmtpEmailSender
from app.infrastructure.jwt.access_tokens import JwtAccessTokenIssuer
from app.infrastructure.jwt.keys import SigningKey, load_signing_key
from app.infrastructure.notifications.rabbitmq import NotificationServiceCodeSender
from app.infrastructure.oauth.client import HttpxOAuthClient
from app.infrastructure.redis.confirmation_codes import RedisConfirmationCodes
from app.infrastructure.redis.login_attempts import RedisLoginAttempts
from app.infrastructure.redis.oauth_state_store import RedisOAuthStateStore
from app.infrastructure.redis.session_store import RedisSessionStore
from app.infrastructure.sqlalchemy.repo.oauth_account_repo import (
    SqlalchemyOAuthAccountRepo,
)
from app.infrastructure.sqlalchemy.repo.password_credential_repo import (
    SqlalchemyPasswordCredentialRepo,
)
from app.infrastructure.sqlalchemy.repo.user_repo import SqlalchemyUserRepo
from app.infrastructure.sqlalchemy.sqlalchemy import make_engine, make_sessionmaker
from app.infrastructure.sqlalchemy.unit_of_work import SqlalchemyUnitOfWork


def make_code_sender(
    settings: Settings, email_sender: EmailSender | None = None
) -> CodeSender:
    """The codes go to the notification service, or out as emails from here
    (``email_sender``, or the one the settings name)."""
    if settings.email_backend is EmailBackend.NOTIFICATIONS and email_sender is None:
        return NotificationServiceCodeSender(settings.rabbitmq_url)
    if email_sender is None:
        if settings.email_backend is EmailBackend.SMTP:
            email_sender = SmtpEmailSender(
                host=settings.smtp_host,
                port=settings.smtp_port,
                sender=settings.email_from,
                username=settings.smtp_username,
                password=settings.smtp_password,
                security=settings.smtp_security,
            )
        else:
            email_sender = ConsoleEmailSender()
    return EmailCodeSender(email_sender)


class Container:
    def __init__(
        self,
        settings: Settings,
        *,
        engine: AsyncEngine | None = None,
        redis: Redis | None = None,
        http: httpx.AsyncClient | None = None,
        email_sender: EmailSender | None = None,
        signing_key: SigningKey | None = None,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        """Every argument after ``settings`` replaces the adapter made from
        the settings (the tests use this)."""
        self.settings = settings
        self.engine = engine or make_engine(settings.database_url)
        self.sessionmaker: async_sessionmaker[AsyncSession] = make_sessionmaker(
            self.engine
        )
        self.redis: Redis = redis or Redis.from_url(
            settings.redis_url, decode_responses=True
        )
        self.http = http or httpx.AsyncClient(timeout=10)
        self.code_sender = make_code_sender(settings, email_sender)
        self.signing_key = signing_key or load_signing_key(
            settings.jwt_private_key,
            settings.jwt_private_key_file,
            settings.jwt_generate_key,
        )
        self.password_hasher = password_hasher or BcryptPasswordHasher()
        self.access_tokens: AccessTokenIssuer = JwtAccessTokenIssuer(
            self.signing_key,
            issuer=settings.public_url,
            audience=settings.jwt_audience,
            lifetime=timedelta(minutes=settings.access_token_lifetime_minutes),
        )
        self.sessions = RedisSessionStore(
            self.redis, timedelta(days=settings.refresh_token_lifetime_days)
        )
        self.confirmation_codes = RedisConfirmationCodes(self.redis)
        self.login_attempts = RedisLoginAttempts(self.redis)
        self.oauth_state_store = RedisOAuthStateStore(self.redis)
        self.oauth_client: OAuthClient = HttpxOAuthClient(
            self.http, settings.google_client_id, settings.google_client_secret
        )

        self.check_user_token = CheckUserToken(self.access_tokens)
        self.list_oauth_providers = ListOAuthProviders(self.oauth_client)
        self.logout = Logout(self.sessions)
        self.logout_all = LogoutAll(self.sessions)
        self.initiate_oauth = InitiateOAuth(
            self.oauth_client,
            self.oauth_state_store,
            settings.oauth_redirect_uris,
        )

    def request(self, session: AsyncSession) -> "RequestContainer":
        return RequestContainer(self, session)

    async def close(self) -> None:
        await self.http.aclose()
        if isinstance(self.code_sender, NotificationServiceCodeSender):
            await self.code_sender.close()
        await self.redis.aclose()
        await self.engine.dispose()


class RequestContainer:
    def __init__(self, app: Container, session: AsyncSession) -> None:
        self.app = app
        user_repo = SqlalchemyUserRepo(session)
        password_credential_repo = SqlalchemyPasswordCredentialRepo(session)
        oauth_account_repo = SqlalchemyOAuthAccountRepo(session)
        unit_of_work = SqlalchemyUnitOfWork(session)

        self.register_user = RegisterUser(
            user_repo=user_repo,
            password_credential_repo=password_credential_repo,
            password_hasher=app.password_hasher,
            unit_of_work=unit_of_work,
            confirmation_codes=app.confirmation_codes,
            code_sender=app.code_sender,
        )
        self.confirm_email = ConfirmEmail(
            confirmation_codes=app.confirmation_codes,
            user_repo=user_repo,
            unit_of_work=unit_of_work,
        )
        self.resend_confirmation = ResendConfirmation(
            user_repo=user_repo,
            confirmation_codes=app.confirmation_codes,
            code_sender=app.code_sender,
        )
        self.authenticate_user = AuthenticateUser(
            user_repo=user_repo,
            password_credential_repo=password_credential_repo,
            password_hasher=app.password_hasher,
            login_attempts=app.login_attempts,
            access_tokens=app.access_tokens,
            sessions=app.sessions,
        )
        self.refresh_user_token = RefreshUserToken(
            sessions=app.sessions,
            access_tokens=app.access_tokens,
            user_repo=user_repo,
        )
        self.get_account = GetAccount(
            user_repo=user_repo,
            password_credential_repo=password_credential_repo,
            oauth_account_repo=oauth_account_repo,
        )
        self.update_account = UpdateAccount(
            user_repo=user_repo, unit_of_work=unit_of_work
        )
        self.delete_user = DeleteUser(
            user_repo=user_repo,
            unit_of_work=unit_of_work,
            sessions=app.sessions,
        )
        self.request_password_reset = RequestPasswordReset(
            user_repo=user_repo,
            confirmation_codes=app.confirmation_codes,
            code_sender=app.code_sender,
        )
        self.reset_password = ResetPassword(
            confirmation_codes=app.confirmation_codes,
            password_hasher=app.password_hasher,
            user_repo=user_repo,
            password_credential_repo=password_credential_repo,
            unit_of_work=unit_of_work,
            sessions=app.sessions,
        )
        self.authenticate_oauth = AuthenticateOAuth(
            oauth_client=app.oauth_client,
            oauth_state_store=app.oauth_state_store,
            oauth_account_repo=oauth_account_repo,
            user_repo=user_repo,
            password_credential_repo=password_credential_repo,
            unit_of_work=unit_of_work,
            access_tokens=app.access_tokens,
            sessions=app.sessions,
        )
        self.unlink_oauth = UnlinkOAuthAccount(
            oauth_account_repo=oauth_account_repo,
            password_credential_repo=password_credential_repo,
            unit_of_work=unit_of_work,
        )
