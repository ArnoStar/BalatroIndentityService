from enum import StrEnum
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class EmailBackend(StrEnum):
    CONSOLE = "console"  # writes the emails to the log (development)
    SMTP = "smtp"
    RABBITMQ = "rabbitmq"  # publishes them for a mail worker


class Settings(BaseSettings):
    """Every setting is an environment variable of the same name in upper
    case (or a line of ``.env``). See ``.env.example``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # the service's public base URL: the tokens' issuer (``iss``)
    public_url: str = "http://localhost:8001"
    # browsers' origins allowed to call the service (comma separated)
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5174",  # the portal (npm run dev)
        "http://localhost:5173",  # the game (npm run dev)
        "http://localhost:8087",  # both, in Docker
    ]

    # (the defaults are `make services`: the game compose file's identity-db and
    # identity-redis)
    database_url: str = (
        "postgresql+asyncpg://identity:identity@localhost:55432/identity"
    )
    redis_url: str = "redis://localhost:56379/0"

    # RS256 signing key: PEM text, or a file (made on the first start when
    # missing and jwt_generate_key is true)
    jwt_private_key: str | None = None
    jwt_private_key_file: str = "keys/jwt_private.pem"
    jwt_generate_key: bool = True
    # who the access tokens are for (``aud``), checked by BalatroWebAPI
    jwt_audience: str = "balatro"
    access_token_lifetime_minutes: int = 15
    refresh_token_lifetime_days: int = 30

    email_backend: EmailBackend = EmailBackend.CONSOLE
    email_from: str = "Balatro <no-reply@localhost>"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    # "starttls" (port 587), "ssl" (port 465) or "none"
    smtp_security: str = "starttls"
    rabbitmq_url: str = "amqp://guest:guest@localhost/"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    # where a provider may send the browser back to (the front end's
    # callback page), comma separated; each one must also be registered
    # with the provider
    oauth_redirect_uris: Annotated[list[str], NoDecode] = [
        "http://localhost:5174/auth/callback",
        "http://localhost:8087/auth/callback",
    ]

    @field_validator("cors_origins", "oauth_redirect_uris", mode="before")
    @classmethod
    def _split_commas(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "jwt_private_key",
        "smtp_username",
        "smtp_password",
        "google_client_id",
        "google_client_secret",
        mode="before",
    )
    @classmethod
    def _empty_is_none(cls, value: Any) -> Any:
        return None if value == "" else value

    @field_validator("public_url")
    @classmethod
    def _no_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


def get_settings() -> Settings:
    return Settings()
