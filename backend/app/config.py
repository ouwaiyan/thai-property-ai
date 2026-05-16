from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Thai Estate API"
    DEBUG: bool = True

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/thai_estate_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/thai_estate_db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-256-bit-key-thai-estate"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Upload
    UPLOAD_DIR: str = "uploads/properties"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Geocoding
    GEOCODING_PROVIDER: str = "nominatim"
    GOOGLE_MAPS_API_KEY: str = ""

    # Route Matrix (Google Routes API)
    ROUTING_PROVIDER: str = "google_routes"
    ROUTE_MATRIX_MAX_CANDIDATES: int = 50
    ROUTE_MATRIX_CACHE_TTL_DAYS: int = 30
    ROUTE_MATRIX_DAILY_API_LIMIT: int = 100

    # AI / OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_REQUEST_TIMEOUT_SECONDS: int = 60

    # LINE Messaging API
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # Storage (local or S3-compatible)
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    S3_ENDPOINT_URL: str = ""       # R2/S3 endpoint, e.g. https://<account>.r2.cloudflarestorage.com
    S3_BUCKET_NAME: str = "thaiestate"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "auto"
    S3_PUBLIC_URL_PREFIX: str = ""  # CDN or public bucket URL prefix

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # n8n Automation
    N8N_WEBHOOK_URL: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
