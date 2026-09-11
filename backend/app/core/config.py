from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application & Environment (Phase 22)
    APP_ENV: str = "development"  # "development" | "staging" | "production" | "test"
    APP_NAME: str = "AnalyzaX"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "development-secret-key-change-in-production"
    RELEASE_VERSION: str = "1.0.0"
    RELEASE_COMMIT_SHA: str = "HEAD"
    BUILD_TIMESTAMP: str = "2026-09-10T12:00:00Z"

    # API Server & Networking
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,::1"

    # PostgreSQL Metadata Database & Connection Pooling
    DATABASE_URL: str = (
        "postgresql+asyncpg://analyzax:analyzax_secure_password@localhost:5432/analyzax_metadata"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_STATEMENT_TIMEOUT_MS: int = 30000

    # Production Storage & Object Store (Phase 22)
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET_NAME: str = "analyzax-data"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "us-east-1"
    STORAGE_SIGN_EXPIRY_SECONDS: int = 3600

    # Observability, Structured Logging & Metrics (Phase 22)
    LOG_FORMAT: str = "text"  # "text" | "json"
    LOG_REDACT_SENSITIVE: bool = True
    METRICS_ENABLED: bool = True

    # Security Headers, Cookies & Rate Limiting (Phase 22)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_RPM: int = 120
    RATE_LIMIT_AUTH_RPM: int = 10
    RATE_LIMIT_AI_RPM: int = 20
    RATE_LIMIT_SQL_RPM: int = 30
    RATE_LIMIT_EXPORT_RPM: int = 15
    RATE_LIMIT_UPLOAD_RPM: int = 20
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE_SECONDS: int = 31536000
    SECURE_COOKIES: bool = False

    # Production Asynchronous Jobs & Workers (Phase 22)
    DATA_JOBS_DIR: str = "./data/jobs"
    JOB_MAX_CONCURRENT_WORKERS: int = 4
    JOB_DEFAULT_TIMEOUT_SECONDS: int = 300
    JOB_DEFAULT_MAX_RETRIES: int = 3
    JOB_RETRY_BACKOFF_BASE_SECONDS: float = 2.0
    JOB_DLQ_RETENTION_DAYS: int = 14

    # Storage Paths
    DATA_STORAGE_ROOT: str = "./data"
    DATA_UPLOADS_DIR: str = "./data/uploads"
    DATA_PROCESSED_DIR: str = "./data/processed"
    DATA_PROFILES_DIR: str = "./data/profiles"
    DATA_QUALITY_DIR: str = "./data/quality"
    DATA_PLANS_DIR: str = "./data/plans"
    DATA_LINEAGE_DIR: str = "./data/lineage"
    DATA_EDA_DIR: str = "./data/eda"
    DATA_SQL_DIR: str = "./data/sql"
    DATA_VISUALIZATIONS_DIR: str = "./data/visualizations"
    DATA_STATISTICS_DIR: str = "./data/statistics"
    DATA_ML_DIR: str = "./data/ml"
    DATA_MODELS_DIR: str = "./data/models"
    DATA_FORECASTING_DIR: str = "./data/forecasting"
    DATA_FORECASTING_MODELS_DIR: str = "./data/forecasting/models"
    DATA_AI_ANALYST_DIR: str = "./data/ai_analyst"
    DATA_DASHBOARDS_DIR: str = "./data/dashboards"
    DATA_EXPORTS_DIR: str = "./data/exports"
    DATA_WORKSPACE_DIR: str = "./data/workspace"
    DATA_AUTH_DIR: str = "./data/auth"
    DATA_COLLABORATION_DIR: str = "./data/collaboration"
    DATA_NOTIFICATIONS_DIR: str = "./data/notifications"
    DATA_USAGE_DIR: str = "./data/usage"
    DATA_BILLING_DIR: str = "./data/billing"
    DATA_TEMP_DIR: str = "./data/temp"

    # Billing & Subscriptions Controls (Phase 21)
    BILLING_ENABLED: bool = True
    BILLING_PROVIDER: str = "sandbox"  # "sandbox" | "mock" | "stripe"
    BILLING_SECRET_KEY: str = ""
    BILLING_WEBHOOK_SECRET: str = "whsec_sandbox_secret_key_analyzax"
    BILLING_PORTAL_RETURN_URL: str = "http://localhost:3000/settings/billing"
    BILLING_CURRENCY: str = "USD"
    BILLING_GRACE_PERIOD_DAYS: int = 7

    # Notification & Activity Controls (Phase 19)
    NOTIFICATION_RETENTION_DAYS: int = 30
    NOTIFICATION_MAX_PER_USER: int = 500
    NOTIFICATION_CLEANUP_BATCH_SIZE: int = 100

    # Authentication & Authorization Controls (Phase 17)
    AUTH_PASSWORD_MIN_LENGTH: int = 8
    AUTH_PASSWORD_MAX_LENGTH: int = 128
    AUTH_SESSION_COOKIE_NAME: str = "analyzax_session"
    AUTH_SESSION_TTL_SECONDS: int = 86400 * 7  # 7 days
    AUTH_ACCESS_TOKEN_TTL_MINUTES: int = 60
    AUTH_LOGIN_MAX_ATTEMPTS: int = 5
    AUTH_LOGIN_WINDOW_SECONDS: int = 300  # 5 minutes
    AUTH_LOGIN_LOCKOUT_SECONDS: int = 900  # 15 minutes
    AUTH_RESET_TOKEN_TTL_SECONDS: int = 3600  # 1 hour
    AUTH_SESSION_SECRET: str = "analyzax-secure-session-secret-change-in-production"

    # Workspace & Project Controls (Phase 16)
    WORKSPACE_MAX_PROJECTS: int = 100
    PROJECT_ACTIVITY_RETENTION_DAYS: int = 90
    PROJECT_MAX_TAGS_PER_ASSET: int = 15
    SEARCH_MAX_RESULTS: int = 100

    # Dashboard Controls & Governance (Phase 14)
    DASHBOARD_MAX_COMPONENTS: int = 50
    DASHBOARD_MAX_FILTERS: int = 20
    DASHBOARD_MAX_LAYOUT_SIZE: int = 100_000
    DASHBOARD_MAX_TABLE_ROWS: int = 500
    DASHBOARD_MAX_DATA_BYTES: int = 10_000_000
    DASHBOARD_MAX_REFRESH_CONCURRENCY: int = 5
    DASHBOARD_MAX_HISTORY_VERSIONS: int = 50
    DASHBOARD_MAX_ACTIONS_PER_REQUEST: int = 10

    # Export & Reporting Controls (Phase 15)
    EXPORT_MAX_ROWS: int = 500_000
    EXPORT_MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100MB
    EXPORT_MAX_CONCURRENT_JOBS: int = 5
    EXPORT_ARTIFACT_TTL_HOURS: int = 72
    EXPORT_MAX_REPORT_SECTIONS: int = 50
    EXPORT_MAX_TABLE_ROWS_IN_REPORT: int = 200

    # AI Analyst Controls & Governance (Phase 13)
    AI_PROVIDER: str = "mock"  # 'openrouter' or 'mock'
    AI_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    AI_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_API_KEY: str = Field(default="", description="AI Provider API Key")
    AI_MAX_TOKENS: int = 4096
    AI_MAX_INPUT_TOKENS: int = 16000
    AI_MAX_OUTPUT_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.1
    AI_TIMEOUT_SECONDS: int = 60
    AI_MAX_TOOL_CALLS: int = 8
    AI_MAX_RETRIES: int = 2
    AI_MAX_ANALYSIS_SECONDS: int = 120
    AI_MAX_CONTEXT_TOKENS: int = 8000
    AI_MAX_RESULT_ROWS: int = 50
    AI_MAX_RESULT_BYTES: int = 500_000
    AI_MAX_CONCURRENT_ANALYSES: int = 3
    ANALYST_PROMPT_VERSION: str = "analyst_v1"

    # Machine Learning Controls & Governance (Phase 11)
    ML_MAX_ROWS: int = 100_000
    ML_MAX_FEATURES: int = 100
    ML_MAX_TRAINING_TIME_SECONDS: int = 120
    ML_MAX_CV_FOLDS: int = 10
    ML_MAX_SEARCH_ITERATIONS: int = 20
    ML_MAX_MODELS_PER_EXPERIMENT: int = 8
    ML_MAX_ARTIFACT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    ML_MAX_PREDICTION_ROWS: int = 100_000
    ML_MAX_ONE_HOT_CARDINALITY: int = 50
    ML_MAX_CONCURRENT_TRAINING_JOBS: int = 3

    # Forecasting Controls & Governance (Phase 12)
    FORECAST_MAX_ROWS: int = 100_000
    FORECAST_MAX_SERIES: int = 10
    FORECAST_MAX_HORIZON: int = 365
    FORECAST_MAX_LAGS: int = 40
    FORECAST_MAX_VALIDATION_FOLDS: int = 10
    FORECAST_MAX_TRAINING_TIME_SECONDS: int = 120
    FORECAST_MAX_MODELS_PER_EXPERIMENT: int = 8
    FORECAST_MAX_HISTORY_LENGTH: int = 100_000
    FORECAST_MAX_ARTIFACT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    FORECAST_MAX_CONCURRENT_JOBS: int = 3

    # Visualization Controls & Thresholds
    VISUALIZATION_MAX_POINTS: int = 10000
    VISUALIZATION_MAX_CATEGORIES: int = 50
    VISUALIZATION_MAX_SERIES: int = 15
    VISUALIZATION_MAX_DATA_BYTES: int = 10 * 1024 * 1024  # 10MB
    DEFAULT_TOP_N: int = 10
    MAX_CATEGORIES_FOR_BAR: int = 25
    MAX_SERIES_FOR_MULTI_SERIES: int = 10
    MAX_SCATTER_POINTS: int = 5000

    # Upload & Ingestion Controls
    MAX_UPLOAD_SIZE_MB: int = 100
    SUPPORTED_FORMATS: List[str] = ["csv", "xlsx", "json", "parquet"]

    # Profiling Controls
    PROFILE_SAMPLE_SIZE: int = 5
    TOP_CATEGORIES_LIMIT: int = 20
    MAX_EXACT_UNIQUE_VALUES: int = 10000
    PROFILING_VERSION: str = "profile_v1"

    # Data Quality Controls & Thresholds
    QUALITY_REPORT_VERSION: str = "quality_v1"
    QUALITY_MISSING_LOW: float = 1.0        # >= 1% missing -> LOW
    QUALITY_MISSING_MEDIUM: float = 5.0     # >= 5% missing -> MEDIUM
    QUALITY_MISSING_HIGH: float = 20.0      # >= 20% missing -> HIGH
    QUALITY_MISSING_CRITICAL: float = 50.0  # >= 50% missing -> CRITICAL
    QUALITY_NEAR_CONSTANT_THRESHOLD: float = 95.0  # Dominant value frequency >= 95%
    QUALITY_OUTLIER_IQR_MULTIPLIER: float = 1.5    # Standard Tukey IQR multiplier
    QUALITY_HIGH_CARDINALITY_THRESHOLD: float = 0.95  # Cardinality ratio >= 0.95 (non-ID)

    # Transformation & Cleaning Controls
    TRANSFORM_PREVIEW_ROWS: int = 10
    MAX_PREVIEW_ROWS: int = 100
    MAX_ONE_HOT_CARDINALITY: int = 50
    MAX_TRANSFORMATION_STEPS: int = 50

    # EDA Controls
    EDA_VERSION: str = "eda_v1"

    # DuckDB Configuration
    DUCKDB_DATABASE_PATH: str = ":memory:"
    DUCKDB_MEMORY_LIMIT: str = "4GB"
    DUCKDB_THREADS: int = 4

    # AI (OpenRouter - optional for Phase 1)
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API Key")


settings = Settings()
