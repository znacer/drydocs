"""Configuration settings using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # PostgreSQL
    postgres_host: str = Field(default="localhost", min_length=1)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str = Field(default="postgres", min_length=1)
    postgres_password: str = Field(default="password", min_length=1)
    postgres_db: str = Field(default="docmanager", min_length=1)

    # MinIO
    minio_endpoint: str = Field(default="localhost:9000", min_length=1)
    minio_access_key: str = Field(default="minioadmin", min_length=1)
    minio_secret_key: str = Field(default="minioadmin", min_length=1)
    minio_bucket: str = Field(default="documents", min_length=1)
    minio_secure: bool = False

    # Authentication
    better_auth_secret: str = Field(
        default="change-me-in-production-use-32-characters-minimum",
        min_length=16,
        description="Secret key for JWT token signing (must match frontend)",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Async PostgreSQL URL
    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
