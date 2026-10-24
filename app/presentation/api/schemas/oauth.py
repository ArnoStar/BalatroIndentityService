from pydantic import BaseModel, Field

from app.domain.value_object.oauth_provider import OAuthProvider


class ProvidersResponse(BaseModel):
    providers: list[OAuthProvider]


class AuthorizeRequest(BaseModel):
    redirect_uri: str = Field(
        max_length=2048,
        description="where the provider sends the browser back (one of the "
        "server's OAUTH_REDIRECT_URIS)",
    )


class AuthorizeResponse(BaseModel):
    authorization_url: str = Field(description="send the browser there")
    state: str


class CallbackRequest(BaseModel):
    code: str = Field(min_length=1, max_length=4096)
    state: str = Field(min_length=1, max_length=256)
