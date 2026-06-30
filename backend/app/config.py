from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "African Intelligence Cloud"
    app_version: str = "0.1.0"
    app_env: str = "development"
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # World Bank
    worldbank_base_url: str = "https://api.worldbank.org/v2"

    # Dataset storage
    storage_backend: str = "local"
    upload_dir: str = "storage/uploads"
    max_upload_size_mb: int = 50

    # Google Cloud
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    gcs_bucket_name: str = ""
    bigquery_dataset: str = ""

    # Secret Manager — when true, SECRET_KEY and DATABASE_URL are loaded from GCP at startup
    use_secret_manager: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if settings.use_secret_manager:
        from app.services.secret_manager_service import bootstrap_secrets
        bootstrap_secrets(settings)
    return settings
