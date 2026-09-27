from fastapi import APIRouter, Depends

from app.application.dtos.oauth import (
    AuthenticateOAuthInput,
    AuthenticateOAuthOutput,
    InitiateOAuthInput,
    InitiateOAuthOutput,
)
from app.bootstrap.container import RequestContainer
from app.domain.value_object.oauth_provider import OAuthProvider
from app.presentation.api.dependencies import get_container
from app.presentation.api.schemas.auth import (
    AuthenticateOAuthResponse,
    InitiateOAuthRequest,
    InitiateOAuthResponse,
    OAuthProv,
)

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.post("/authenticate", response_model=InitiateOAuthResponse)
async def authenticate(
    request: InitiateOAuthRequest,
    container: RequestContainer = Depends(get_container),
):
    dto: InitiateOAuthInput = InitiateOAuthInput(OAuthProvider(request.provider))

    callback: InitiateOAuthOutput = await container.initiate_oauth.execute(dto)

    return InitiateOAuthResponse(
        state=callback.state, callback_url=callback.callback_url
    )


# To test this endpoint with google
# https://accounts.google.com/o/oauth2/v2/auth?client_id={google_client_id}&redirect_uri=http://localhost:8000/oauth/google/callback&response_type=code&scope=openid%20email%20profile&state={state}
@router.get("/{provider}/callback", response_model=AuthenticateOAuthResponse)
async def callback(
    provider: OAuthProv,
    state: str,
    code: str,
    container: RequestContainer = Depends(get_container),
):
    dto: AuthenticateOAuthInput = AuthenticateOAuthInput(
        provider=OAuthProvider(provider.value),
        state=state,
        code=code,
    )

    tokens: AuthenticateOAuthOutput = await container.authenticate_oauth.execute(dto)

    return AuthenticateOAuthResponse(
        access_token=tokens.token_pair.access_token.value,
        refresh_token=tokens.token_pair.refresh_token.value,
    )
