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
        {"name": "privileges", "description": "Privilege management (fine-grained access rights)"},
        {"name": "roles", "description": "Role management (user roles and associated permissions)"},
        {"name": "samples", "description": "Sample resource management"},
        {"name": "users", "description": "User management"},
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
        "http://localhost:3000", # Common frontend dev port
        "http://localhost:8000"  # Default Uvicorn port if frontend is served by FastAPI itself
    ]
    # In production, this MUST be overridden via environment variables
    # to reflect the actual domain(s) of your frontend application.
    # e.g., BACKEND_CORS_ORIGINS='["https://your-app-domain.com", "https://www.your-app-domain.com"]'

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
    POSTGRES_USER: str = "admin"  # Default for development. Should be changed in .env for production.
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: str = "test"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("POSTGRES_PASSWORD", pre=False)
    def validate_postgres_password(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if not values.get("DEBUG") and values.get("POSTGRES_USER") and not v:
            raise ValueError(
                "POSTGRES_PASSWORD must be set in a production environment (when DEBUG=False) if POSTGRES_USER is set."
            )
        return v

    # DragonFlyDB (Redis-compatible) settings
    DRAGONFLY_HOST: str = "localhost"
    DRAGONFLY_PORT: int = 6379
    DRAGONFLY_DB: int = 0
    DRAGONFLY_PASSWORD: Optional[str] = None

    # JWT settings
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ISSUER: str = "your_jwt_issuer"  # Default for development. Should be changed in .env for production.
    JWT_AUDIENCE: str = "your_jwt_audience"  # Default for development. Should be changed in .env for production.
    JWT_EXPIRATION: int = 30  # in minutes
    JWT_REFRESH_EXPIRATION: int = 7  # in days
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_TYPE: str = "Bearer"
    JWT_TOKEN_PREFIX: str = "CB "
    ALGORITHM: str = "HS256"

    @validator("JWT_SECRET_KEY", pre=False)
    def validate_jwt_secret_key(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if not values.get("DEBUG") and not v:
            raise ValueError("JWT_SECRET_KEY must be set in a production environment (when DEBUG=False).")
        if values.get("DEBUG") and not v:
            print(
                "WARNING: JWT_SECRET_KEY is not set. Using a default insecure key for DEBUG mode. "
                "SET THIS IN YOUR .env FILE for security, even in development."
            )
            return "insecure_debug_key_please_replace"
        return v

    # Google OAuth2 settings (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None  # Optional: Configure via env var if Google OAuth is used.
    GOOGLE_CLIENT_SECRET: Optional[str] = None # Optional: Configure via env var if Google OAuth is used.
    GOOGLE_REDIRECT_URI: Optional[str] = None # Optional: Configure via env var if Google OAuth is used.
    GOOGLE_SECRET_KEY: Optional[str] = None # This is an unusual name, typically GOOGLE_CLIENT_SECRET is the primary secret.
                                          # If this is a distinct secret (e.g., for API key), configure via env var if used.

    @validator("GOOGLE_SECRET_KEY", pre=False)
    def validate_google_secret_key(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if not values.get("DEBUG") and values.get("GOOGLE_CLIENT_ID") and not v:
            raise ValueError(
                "GOOGLE_SECRET_KEY must be set in a production environment (when DEBUG=False) if GOOGLE_CLIENT_ID is set."
            )
        # No default for GOOGLE_SECRET_KEY in debug, as it's less critical for basic app runnability than JWT_SECRET_KEY
        # and highly dependent on whether Google OAuth is actively being developed/tested.
        return v

    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None  # Optional: Configure via env var if email sending is used.
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: List[str] = ["localhost:9092"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
