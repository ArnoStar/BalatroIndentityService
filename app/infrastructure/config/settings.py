from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    sql_database_url: str = "postgresql+asyncpg://postgres:your_secure_password@localhost:5432/indentityservice"

    redis_host: str = "localhost"
    redis_port: int = 6379

    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    access_jwt_lifetime_minutes: int = 15
    refresh_jwt_lifetime_days: int = 30

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None


settings = _Settings()
