import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.application.dtos.tokens import AccessToken
from app.application.exceptions.token import InvalidToken
from app.application.ports.token_issuer import AccessTokenIssuer
from app.domain.entities.user import User
from app.infrastructure.jwt.keys import SigningKey


class JwtAccessTokenIssuer(AccessTokenIssuer):
    """Access tokens are RS256 JWTs:
    ``{iss, aud, sub: user id, name: display name, roles: [role...], iat, exp,
    jti, typ: "access"}``."""

    def __init__(
        self,
        key: SigningKey,
        issuer: str,
        audience: str,
        lifetime: timedelta,
    ) -> None:
        self.key = key
        self.issuer = issuer
        self.audience = audience
        self.lifetime = lifetime

    def issue(self, user: User) -> AccessToken:
        now = datetime.now(UTC)
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": str(user.id),
            "name": user.display_name.value,
            "roles": sorted(r.value for r in user.roles),
            "iat": now,
            "exp": now + self.lifetime,
            "jti": uuid.uuid4().hex,
            "typ": "access",
        }
        token = jwt.encode(
            payload,
            self.key.private_key,
            algorithm="RS256",
            headers={"kid": self.key.kid},
        )
        return AccessToken(token, int(self.lifetime.total_seconds()))

    def verify(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                self.key.private_key.public_key(),
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
            if payload.get("typ") != "access":
                raise InvalidToken
            return UUID(payload["sub"])
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise InvalidToken from exc
