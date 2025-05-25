# cache/manager.py

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from cache.system import CacheSystem
from cache.system import CacheSystem

class CacheMiddleware(BaseHTTPMiddleware):
    """Simple passthrough; all logic is in decorator."""
    async def dispatch(self, request, call_next):
        return await call_next(request)

class CacheManager:
    def __init__(self, app: FastAPI):
        self.system = CacheSystem()
        app.state.cache_system = self.system
        # we keep middleware for future global caching needs
        app.add_middleware(CacheMiddleware)
