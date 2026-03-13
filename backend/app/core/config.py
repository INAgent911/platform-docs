from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MSP Platform API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"

    secret_key: str = "change-me-in-env"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "postgresql+psycopg://platform:platform@db:5432/platform"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    bootstrap_enabled: bool = True
    bootstrap_tenant_name: str = "Demo MSP"
    bootstrap_tenant_slug: str = "demo-msp"
    bootstrap_owner_email: str = "owner@demo-msp.com"
    bootstrap_owner_password: str = "ChangeMe123!"
    bootstrap_owner_first_name: str = "Platform"
    bootstrap_owner_last_name: str = "Owner"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
