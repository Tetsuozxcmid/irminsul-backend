from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    YANDEX_REDIRECT_URI: str

    VK_CALLBACK: str
    VK_APP_ID: int
    VK_APP_SECRET: str

    FRONTEND_URL: str

    JWT_SECRET: str

    # Внутренний ключ для POST /api/notifications (заголовок X-Internal-Key)
    NOTIFICATIONS_INTERNAL_KEY: str = ""

    # CORS: через запятую; пусто — FRONTEND_URL + localhost
    CORS_ORIGINS: str = ""

    # Cookies: Domain=.irminsul.space для общего домена фронта и api
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = True
    # none | lax | strict (none нужен при cross-subdomain fetch с credentials)
    COOKIE_SAMESITE: str = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins(self) -> list[str]:
        origins: set[str] = set()

        frontend = self.FRONTEND_URL.strip().rstrip("/")
        if frontend:
            origins.add(frontend)

        raw = self.CORS_ORIGINS.strip()
        if raw:
            for item in raw.split(","):
                value = item.strip().rstrip("/")
                if value:
                    origins.add(value)

        if not origins:
            origins.update(
                {
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                }
            )

        for origin in list(origins):
            if origin.startswith("https://") and "://www." not in origin:
                origins.add(origin.replace("https://", "https://www.", 1))

        return sorted(origins)

    @property
    def cookie_samesite(self) -> str:
        value = self.COOKIE_SAMESITE.strip().lower()
        if value in {"none", "lax", "strict"}:
            return value.capitalize() if value != "none" else "None"
        return "Lax"


settings = Settings()
