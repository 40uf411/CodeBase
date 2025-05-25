import time
from typing import Any, Dict
from fastapi import APIRouter, Depends, status, Request

from core.auth import require_privileges
from core.database import get_db

router = APIRouter(
    prefix="/cache",
    tags=["cache"],
    dependencies=[ require_privileges("cache:read") ],
)

@router.get(
    "/config",
    summary="Get cache configuration"
)
async def get_cache_config(request: Request) -> Dict[str, Any]:
    return {"cache_config": request.app.state.cache_system.get_cache_config()}

@router.post(
    "/configure/{path:path}",
    dependencies=[ require_privileges("cache:update") ],
    summary="Configure cache for a route"
)
async def configure_route_cache(
    path: str,
    duration: int,
    request: Request
) -> Dict[str, Any]:
    request.app.state.cache_system.configure_route_cache(f"/{path}", duration)
    return {
        "message": f"Cache configured for /{path} ({duration}s)",
        "path": f"/{path}",
        "duration": duration
    }

@router.delete(
    "/clear",
    dependencies=[ require_privileges("cache:delete") ],
    summary="Clear all cache"
)
async def clear_all_cache(request: Request) -> Dict[str, Any]:
    request.app.state.cache_system.clear_cache()
    return {"message": "All caches cleared"}

@router.delete(
    "/clear/{path:path}",
    dependencies=[ require_privileges("cache:delete") ],
    summary="Clear cache for a route"
)
async def clear_route_cache(path: str, request: Request) -> Dict[str, Any]:
    request.app.state.cache_system.clear_cache(f"/{path}")
    return {"message": f"Cache cleared for /{path}", "path": f"/{path}"}

# Cached example with protection
@router.get(
    "/example",
    summary="Cached example",
    dependencies=[ require_privileges("cache:read") ],
)

async def cached_example(request: Request) -> Dict[str, Any]:
    return {
        "message": "This response is cached for 60 seconds",
        "user": request.state.user.email,
        "timestamp": time.time()
    }
