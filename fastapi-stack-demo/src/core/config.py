from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SRC_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = (
    SRC_DIR.parent / ".env"
)  # только для локальной разработки; в проде — переменные окружения


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        env_prefix="FASTAPI_",
        extra="ignore",
    )

    app_env: str = "local"
    debug: bool

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr
    postgres_host: str
    postgres_port: int = 5432
    database_pool_size: int = 5
    database_max_overflow: int = 5
    sql_echo: bool = False

    redis_host: str
    redis_port: int = 6379
    redis_password: SecretStr

    # JSON-список, например ["http://localhost:5173"]. В проде за одним доменом не нужен.
    cors_origins: list[str] = []
    ws_heartbeat_seconds: int = 15

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_must_be_long(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("FASTAPI_JWT_SECRET_KEY должен быть не короче 32 символов")
        return value

    def redis_url(self, db: int = 0) -> str:
        password = quote(self.redis_password.get_secret_value(), safe="")
        return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
