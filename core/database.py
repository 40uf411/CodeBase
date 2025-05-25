from typing import Generator
import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .config import settings

# PostgreSQL setup
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DragonFlyDB (Redis-compatible) setup
redis_client = redis.Redis(
    host=settings.DRAGONFLY_HOST,
    port=settings.DRAGONFLY_PORT,
    db=settings.DRAGONFLY_DB,
    password=settings.DRAGONFLY_PASSWORD,
    decode_responses=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> Generator[redis.Redis, None, None]:
    """
    Dependency for getting a Redis client.
    """
    try:
        yield redis_client
    finally:
        # Redis connections are returned to the connection pool automatically
        pass
