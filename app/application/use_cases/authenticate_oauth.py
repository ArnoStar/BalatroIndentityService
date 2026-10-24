from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.dtos.oauth import AuthenticateOAuthInput, OAuthIdentity
from app.application.dtos.tokens import TokenPair
from app.application.exceptions.oauth import (
    InvalidOAuthState,
    OAuthAccountConflict,
    OAuthAccountInUse,
    OAuthEmailNotVerified,
)
from app.application.ports.oauth.oauth_client import OAuthClient
from app.application.ports.oauth.oauth_state_store import OAuthStateStore
from app.application.ports.repo.oauth_account_repo import OAuthAccountRepo
from app.application.ports.repo.password_credential_repo import (
    PasswordCredentialRepo,
)
from app.application.ports.repo.user_repo import UserRepo
from app.application.ports.session_store import SessionStore
from app.application.ports.token_issuer import AccessTokenIssuer
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases._shared import issue_tokens
from app.domain.entities.oauth_account import OAuthAccount
from app.domain.entities.user import User
from app.domain.value_object.display_name import DisplayName


class AuthenticateOAuth:
    """Signs in with a provider's authorization code. A new provider account
    is linked to the user with the same (verified) email, or makes a new user
    (named after the provider's profile). When a signed-in user started the
    flow to link the provider (``link_to``), it is linked to them instead."""

    def __init__(
        self,
        oauth_client: OAuthClient,
        oauth_state_store: OAuthStateStore,
        oauth_account_repo: OAuthAccountRepo,
        user_repo: UserRepo,
        password_credential_repo: PasswordCredentialRepo,
        unit_of_work: UnitOfWork,
        access_tokens: AccessTokenIssuer,
        sessions: SessionStore,
    ) -> None:
        self.oauth_client = oauth_client
        self.oauth_state_store = oauth_state_store
        self.oauth_account_repo = oauth_account_repo
        self.user_repo = user_repo
        self.password_credential_repo = password_credential_repo
        self.unit_of_work = unit_of_work
        self.access_tokens = access_tokens
        self.sessions = sessions

    async def execute(self, dto: AuthenticateOAuthInput) -> TokenPair:
        pending = await self.oauth_state_store.pop(dto.state)

        if pending is None or pending.provider != dto.provider:
            raise InvalidOAuthState

        identity = await self.oauth_client.exchange(
            provider=dto.provider,
            code=dto.code,
            code_verifier=pending.code_verifier,
            redirect_uri=pending.redirect_uri,
        )

        oauth_account = await self.oauth_account_repo.get_by_provider(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        )

        if pending.link_to is not None:
            return await self._link(pending.link_to, identity, oauth_account)

        if oauth_account is not None:
            linked_user = await self.user_repo.get_by_id(oauth_account.user_id)
            if linked_user is None:  # (deleted meanwhile)
                raise InvalidOAuthState
            return await issue_tokens(self.access_tokens, self.sessions, linked_user)

        # linking by email is only safe when the provider vouches for it
        if not identity.email_verified:
            raise OAuthEmailNotVerified

        user = await self.user_repo.get_by_email(identity.email)
        now = datetime.now(UTC)

        if user is None:
            user = User(
                id=uuid4(),
                email=identity.email,
                display_name=DisplayName.from_profile(identity.name),
                email_verified_at=now,
                created_at=now,
                updated_at=now,
            )
            await self.user_repo.create(user)
        else:
            linked = await self.oauth_account_repo.get_by_user_id(
                identity.provider, user.id
            )
            if linked is not None:
                raise OAuthAccountConflict

            if not user.email_verified:
                # someone registered this address without proving they own it:
                # their password must not open the real owner's account
                await self.password_credential_repo.delete_by_user_id(user.id)
                await self.user_repo.verify_email(user.id, now)

        await self._create_link(user, identity)
        await self.unit_of_work.commit()

        return await issue_tokens(self.access_tokens, self.sessions, user)

    async def _link(
        self,
        user_id: UUID,
        identity: OAuthIdentity,
        oauth_account: OAuthAccount | None,
    ) -> TokenPair:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:  # (deleted meanwhile)
            raise InvalidOAuthState

        if oauth_account is not None:
            if oauth_account.user_id != user.id:
                raise OAuthAccountInUse
            # (linked already: nothing to do)
            return await issue_tokens(self.access_tokens, self.sessions, user)

        if await self.oauth_account_repo.get_by_user_id(identity.provider, user.id):
            raise OAuthAccountConflict

        await self._create_link(user, identity)
        await self.unit_of_work.commit()
        return await issue_tokens(self.access_tokens, self.sessions, user)

    async def _create_link(self, user: User, identity: OAuthIdentity) -> None:
        now = datetime.now(UTC)
        await self.oauth_account_repo.create(
            OAuthAccount(
                id=uuid4(),
                user_id=user.id,
                provider=identity.provider,
                provider_user_id=identity.provider_user_id,
                created_at=now,
                updated_at=now,
            )
        )
