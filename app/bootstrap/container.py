from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.use_cases.register_user import RegisterUser
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

        # Use cases

        self.register_user: RegisterUser = RegisterUser(
            user_repo=self.user_repo,
        )
