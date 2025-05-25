# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import engine, Base
from cache.manager import CacheManager
from routers import register_routers

def get_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.PROJECT_VER_STR}/openapi.json",
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        terms_of_service=settings.PROJECTS_TERMS_OF_SERVICE,
        contact=settings.PROJECTS_CONTACT,
        license_info=settings.PROJECT_LICENSE_INFO,
    )

    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
