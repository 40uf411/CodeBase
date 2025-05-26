# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import SessionLocal # Assuming SessionLocal is your session factory
# from core.database import engine, Base # Unused in main.py
from cache.manager import CacheManager
from routers import register_routers
from middleware.activity_logging_middleware import ActivityLoggingMiddleware
from services.activity_logger_service import ActivityLoggerService # Import the service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = None
    try:
        db = SessionLocal()
        # Initialize ActivityLoggerService with a DB session.
        # This will also call initialize_default_settings within ActivityLoggerService.
        logger_instance = ActivityLoggerService(db=db) 
        app.state.activity_logger_service = logger_instance # Store instance on app.state
        print("Application startup: ActivityLoggerService initialized, default logging settings ensured, and instance stored on app.state.")
    except Exception as e:
        # Handle exceptions during startup, e.g., DB connection errors
        print(f"Error during application startup: {e}")
        # Optionally, re-raise or exit if critical
    finally:
        if db:
            db.close()
    
    yield
    
    # Shutdown (if any cleanup needed)
    print("Application shutdown.")


def get_application() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan, # Use the new lifespan context manager
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.PROJECT_VER_STR}/openapi.json",
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        terms_of_service=settings.PROJECTS_TERMS_OF_SERVICE,
        contact=settings.PROJECTS_CONTACT,
        license_info=settings.PROJECT_LICENSE_INFO,
    )

    # Database schema management
    # --------------------------
    # Database tables are managed via Alembic migrations.
    # To initialize the database schema for the first time or to apply pending migrations,
    # run the following Alembic command:
    #
    # alembic upgrade head
    #
    # This command should be part of your deployment process and development setup.
    # Automatic table creation (Base.metadata.create_all) has been removed from application
    # startup to promote a more controlled and explicit schema management practice.
    # For development, ensure you run 'alembic upgrade head' after setting up your database
    # and before running the application for the first time.

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Activity Logging Middleware
    # This is added after CORS. It will log requests that have passed CORS checks.
    app.add_middleware(ActivityLoggingMiddleware)

    # health & misc
    @app.get("/")
    async def root():
        return {"message": "Welcome"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/version")
    async def version():
        return {"version": settings.PROJECT_VERSION}
    
    # Initialize cache system
    CacheManager(app)

    # include your routers (see next section)
    register_routers(app)

    return app

app = get_application()

from oauths.google_oauth import GoogleOAuth
GoogleOAuth(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
