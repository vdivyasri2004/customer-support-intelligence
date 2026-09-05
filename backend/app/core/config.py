import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./csi.db"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"
    AI_PROVIDER: str = "local"
    LOCAL_AI_BASE_URL: str = "http://localhost:11434"
    LOCAL_AI_MODEL: str = ""
    API_AI_BASE_URL: str = ""
    API_AI_KEY: str = ""
    API_AI_MODEL: str = ""
    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
