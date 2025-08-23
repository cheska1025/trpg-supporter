from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "TRPG Supporter"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    DB_URL: str = "sqlite+aiosqlite:///./dev.db"


settings = Settings()
