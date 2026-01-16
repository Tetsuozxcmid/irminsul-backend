from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: int
    DB_NAME: str

    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    YANDEX_REDIRECT_URI: str

    FRONTEND_URL: str
    APP_ENV: str

    JWT_SECRET: str





    model_config = SettingsConfigDict(
        env_file=".env",  
        env_file_encoding="utf-8",
        extra="ignore"  
    )

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
settings = Settings() 