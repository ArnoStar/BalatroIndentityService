from fastapi import APIRouter, Response, status

from app.application.dtos.oauth import (
    AuthenticateOAuthInput,
    InitiateOAuthInput,
    UnlinkOAuthAccountInput,
)
from app.domain.value_object.oauth_provider import OAuthProvider
from app.presentation.api.dependencies import AppContainer, CurrentUserId, Uses
from app.presentation.api.schemas.auth import TokenResponse
from app.presentation.api.schemas.oauth import (
    AuthorizeRequest,
    AuthorizeResponse,
    CallbackRequest,
    ProvidersResponse,
)

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/providers", summary="The providers this server can sign in with")
def providers(container: AppContainer) -> ProvidersResponse:
    return ProvidersResponse(providers=container.list_oauth_providers.execute())


@router.post("/{provider}/authorize", summary="Start signing in with a provider")
async def authorize(
    provider: OAuthProvider, body: AuthorizeRequest, container: AppContainer
) -> AuthorizeResponse:
    """Send the browser to ``authorization_url``. The provider sends it back
    to ``redirect_uri`` with ``code`` and ``state`` in the query, which go to
    ``POST /oauth/{provider}/callback``. The state is valid for 10 minutes."""
    output = await container.initiate_oauth.execute(
        InitiateOAuthInput(provider, body.redirect_uri)
    )
    return AuthorizeResponse(
        authorization_url=output.authorization_url, state=output.state
    )


@router.post(
    "/{provider}/link", summary="Start linking a provider to the signed-in account"
)
async def link(
    provider: OAuthProvider,
    body: AuthorizeRequest,
    user_id: CurrentUserId,
    container: AppContainer,
) -> AuthorizeResponse:
    """As ``/authorize``, but the provider's account (whatever its email) is
    linked to the signed-in account when the callback completes. The callback
    answers with tokens for this account. 409 ``oauth_account_in_use`` when
    that provider account belongs to another player."""
    output = await container.initiate_oauth.execute(
        InitiateOAuthInput(provider, body.redirect_uri, link_to=user_id)
    )
    return AuthorizeResponse(
        authorization_url=output.authorization_url, state=output.state
    )


@router.post("/{provider}/callback", summary="Finish signing in with a provider")
async def callback(
    provider: OAuthProvider, body: CallbackRequest, uses: Uses
) -> TokenResponse:
    tokens = await uses.authenticate_oauth.execute(
        AuthenticateOAuthInput(provider=provider, state=body.state, code=body.code)
    )
    return TokenResponse.of(tokens)


@router.delete(
    "/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink a provider from the account",
)
async def unlink(
    provider: OAuthProvider, user_id: CurrentUserId, uses: Uses
) -> Response:
    """Refused (409 ``last_sign_in_method``) when it is the only way left to
    sign in: set a password first (``/auth/password/forgot``)."""
    await uses.unlink_oauth.execute(UnlinkOAuthAccountInput(user_id, provider))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
