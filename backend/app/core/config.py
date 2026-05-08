from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # PostgreSQL Connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "documind"
    POSTGRES_PORT: str = "5432"
    
    # Custom direct URL
    DATABASE_URL_OVERRIDE: Optional[str] = None
    
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
