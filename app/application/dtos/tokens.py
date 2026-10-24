from dataclasses import dataclass


@dataclass(frozen=True)
class AccessToken:
    value: str
    expires_in: int  # seconds


@dataclass(frozen=True)
class TokenPair:
    """What a successful sign-in gives: a short-lived access token (a JWT the
    other services verify with the JWKS) and a refresh token (opaque, single
    use: each refresh returns a new one)."""

    access_token: str
    refresh_token: str
    expires_in: int  # of the access token, in seconds
