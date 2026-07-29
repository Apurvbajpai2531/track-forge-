import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres connection — override via environment variables in production.
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://trackforge:trackforge@localhost:5432/trackforge",
    )
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-prod")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    class Config:
        env_file = ".env"


settings = Settings()
