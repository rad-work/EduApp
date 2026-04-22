import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "EduAppMai")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://eduapp_user:eduapp_password@db:5432/eduapp",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")


settings = Settings()
