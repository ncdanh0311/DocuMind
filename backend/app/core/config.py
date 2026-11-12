from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30 # 30 days
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    OTP_EXPIRE_MINUTES: int = 5
    RESET_TOKEN_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_SEND_COOLDOWN_SECONDS: int = 60
    OTP_SEND_HOURLY_LIMIT: int = 5
    
    # PostgreSQL Connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "documind"
    POSTGRES_PORT: str = "5432"
    
    # Custom direct URL
    DATABASE_URL_OVERRIDE: Optional[str] = None
    DATABASE_DIRECT_URL: Optional[str] = None
    
    # Email Configuration
    EMAILS_FROM_EMAIL: str = "inhtan810@gmail.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "inhtan810@gmail.com"
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAIL_PROVIDER: str = "smtp"
    BREVO_API_KEY: str = ""
    GMAIL_SENDER_EMAIL: str = ""
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REFRESH_TOKEN: str = ""
    
    UPLOAD_DIR: str = ".uploads"
    AI_ENABLED: bool = False
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024
    MAX_USER_STORAGE_BYTES: int = 512 * 1024 * 1024
    MAX_TOTAL_STORAGE_BYTES: int = 2 * 1024 * 1024 * 1024
    MAX_ACTIVE_JOBS_PER_USER: int = 2
    STORAGE_BACKEND: str = "local"
    STORAGE_BUCKET: str = "documind-documents"
    AWS_ENDPOINT_URL_S3: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    EXTRACT_TIMEOUT_SECONDS: int = 15
    EXTRACT_MAX_PAGES: int = 200
    EXTRACT_MAX_CHARACTERS: int = 1000000
    JOB_LEASE_SECONDS: int = 120
    JOB_HEARTBEAT_SECONDS: int = 30
    JOB_MAX_SECONDS: int = 1800
    AI_TIMEOUT_SECONDS: int = 180

    # AI Microservice URL
    AI_SERVICE_URL: str = "http://localhost:8001"
    
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @field_validator("STORAGE_BACKEND")
    @classmethod
    def validate_storage(cls, value: str) -> str:
        if value not in ("local", "neon_s3"):
            raise ValueError("Unsupported storage backend")
        return value

    @field_validator("EMAIL_PROVIDER")
    @classmethod
    def validate_email_provider(cls, value: str) -> str:
        if value not in ("smtp", "brevo", "gmail_api"):
            raise ValueError("Unsupported email provider")
        return value

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if len(value) < 32 or any(marker in value.lower() for marker in ("change", "your-secret", "super-secret")):
            raise ValueError("SECRET_KEY must be a unique random secret of at least 32 characters")
        return value

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only HS256 is supported")
        return value

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore", hide_input_in_errors=True)

settings = Settings()
