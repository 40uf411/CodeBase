from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, PostgresDsn, validator, AnyHttpUrl, EmailStr


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings for environment variable loading.
    """
    # API settings
    PROJECT_VER_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Project"
    PROJECT_DESCRIPTION: str = "A FastAPI project with PostgreSQL and DragonFlyDB"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_TAGS: List[Dict[str, str]] = [
        {"name": "auth", "description": "Authentication and authorization"},
        {"name": "users", "description": "User management"},
        {"name": "items", "description": "Item management"},
    ]
    PROJECTS_TERMS_OF_SERVICE: str = "https://example.com/terms"
    PROJECTS_CONTACT: Dict[str, str] = {
        "name": "Ali Aouf",
        "url": "https://example.com/contact",
        "email": "test@t.com",
    }
    PROJECT_LICENSE_INFO: Dict[str, str] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Security settings
    DEBUG: bool = True
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://example.com",
    ]

    # PostgreSQL database settings
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "6534"
    POSTGRES_DB: str = "test"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    # DragonFlyDB (Redis-compatible) settings
    DRAGONFLY_HOST: str = "localhost"
    DRAGONFLY_PORT: int = 6379
    DRAGONFLY_DB: int = 0
    DRAGONFLY_PASSWORD: Optional[str] = None
    
    # JWT settings
    JWT_SECRET_KEY: str = "your_jwt_secret_key"
    JWT_ISSUER: str = "your_jwt_issuer"
    JWT_AUDIENCE: str = "your_jwt_audience"
    JWT_EXPIRATION: int = 30  # in minutes
    JWT_REFRESH_EXPIRATION: int = 7  # in days
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_TYPE: str = "Bearer"
    JWT_TOKEN_PREFIX: str = "CB "
    ALGORITHM: str = "HS256"
    
    # Google OAuth2 settings (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    GOOGLE_SECRET_KEY: str = "your_google_secret_key"
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: List[str] = ["localhost:9092"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
