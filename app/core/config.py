from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EduAppMai"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+psycopg://eduapp_user:eduapp_password@db:5432/eduapp"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret_key: str = "change_me_for_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    auth_cookie_name: str = "access_token"
    redis_queue_name: str = "submission_queue"
    runner_image: str = "eduapp_runner:latest"
    runner_cpu_limit: float = 0.5
    runner_memory_limit_mb: int = 256
    runner_timeout_sec: int = 2
    project_root: str = "/app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
