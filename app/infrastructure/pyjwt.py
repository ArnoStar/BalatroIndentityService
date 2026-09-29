from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.application.exceptions.token import InvalidToken, WrongTokenType
from app.application.ports.token_issuer import TokenIssuer
from app.domain.entities.token_pair import TokenPair
from app.domain.value_object.tokens import AccessToken, RefreshToken


class PyJwtTokenIssuer(TokenIssuer):
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_lifetime: timedelta = timedelta(minutes=15),
        refresh_token_lifetime: timedelta = timedelta(days=30),
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_lifetime = access_token_lifetime
        self.refresh_token_lifetime = refresh_token_lifetime

    def issue(self, user_id: UUID) -> TokenPair:
        return TokenPair(
            access_token=AccessToken(
                self._create_token(
                    user_id=user_id,
                    token_type="access",
                    lifetime=self.access_token_lifetime,
                )
            ),
            refresh_token=RefreshToken(
                self._create_token(
                    user_id=user_id,
                    token_type="refresh",
                    lifetime=self.refresh_token_lifetime,
                )
            ),
        )

    def refresh(self, refresh_token: RefreshToken) -> TokenPair:
        try:
            payload = jwt.decode(
                refresh_token.value,
                self.secret_key,
                algorithms=[self.algorithm],
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidToken from exc

        if payload.get("type") != "refresh":
            raise WrongTokenType

        user_id = UUID(payload["sub"])

        return self.issue(user_id)

    def check(self, token: AccessToken) -> UUID:
        try:
            payload = jwt.decode(
                token.value,
                self.secret_key,
                algorithms=[self.algorithm],
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidToken from exc

        if payload.get("type") != "access":
            raise WrongTokenType

        return UUID(payload["sub"])

    def _create_token(
        self,
        user_id: UUID,
        token_type: str,
        lifetime: timedelta,
    ) -> str:
        now = datetime.now(UTC)

        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + lifetime,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )
