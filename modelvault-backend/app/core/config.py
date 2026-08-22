from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "ModelVault Backend"
    API_V1_STR: str = ""
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/modelvault"


settings = Settings()
