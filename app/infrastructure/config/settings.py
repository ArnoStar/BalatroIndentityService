from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    sql_database_url: str = "postgresql+asyncpg://postgres:your_secure_password@localhost:5432/indentityservice"


settings = _Settings()
