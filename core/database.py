from typing import Generator, AsyncGenerator # Added AsyncGenerator
import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # Added
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .config import settings

# --- Synchronous PostgreSQL Setup (Deprecated) ---
# This setup is for synchronous database operations and will be phased out.
# Prefer using the asynchronous setup below for new code.
sync_engine = create_engine( # Renamed to sync_engine
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine) # Renamed

# --- Asynchronous PostgreSQL Setup ---
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    # pool_pre_ping=True, # create_async_engine does not support pool_pre_ping directly
    # echo=True, # Optional: for debugging SQL
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False, # Recommended for async sessions
)

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
    (Deprecated) Dependency for getting a synchronous database session.
    Prefer get_async_db for new asynchronous operations.
    """
    db = SyncSessionLocal() # Updated to use SyncSessionLocal
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting an asynchronous database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_redis() -> Generator[redis.Redis, None, None]:
    """
    Dependency for getting a Redis client.
    """
    try:
        yield redis_client
    finally:
        # Redis connections are returned to the connection pool automatically
        pass
