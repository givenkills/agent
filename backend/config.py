import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./game.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-please"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    OPENAI_API_KEY: str = "sk-86f53d20416e46518669d80b3100c944"
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_MODEL: str = "deepseek-v4-flash"

    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
