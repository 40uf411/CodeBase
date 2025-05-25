from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional, Callable
import time
import json

from core.config import settings

class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching API responses.
    
    Features:
    - Route-based caching
    - Configurable cache duration
    - Cache key generation based on request path and query parameters
    """
    
    def __init__(self, app, redis_client):
        super().__init__(app)
        self.redis_client = redis_client
        self.cache_config = {}  # Maps route paths to cache durations in seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if route is configured for caching
        path = request.url.path
        if path not in self.cache_config:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        try:
            cached_response = self.redis_client.get(cache_key)
        except Exception as e:
            # Log error and proceed without cache
            print(f"Cache error: {e}")
            cached_response = None
        if cached_response:
            # Return cached response
            cached_data = json.loads(cached_response)
            return Response(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data["headers"],
                media_type=cached_data["media_type"]
            )
        
        # Get response from route handler
        response = await call_next(request)
        
        # Cache the response
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Create a new response with the same body
        new_response = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        # Only cache successful responses
        if 200 <= response.status_code < 300:
            cache_duration = self.cache_config[path]
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
                "timestamp": time.time()
            }
            try:
                self.redis_client.setex(
                    cache_key,
                    cache_duration,
                    json.dumps(cache_data)
                )
            except Exception as e:
                # Log error if cache write fails
                print(f"Cache write error: {e}")
        
        return new_response
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a cache key based on request path and query parameters.
        
        Args:
            request: FastAPI request
            
        Returns:
            Cache key string
        """
        path = request.url.path
        query_string = request.url.query
        return f"cache:{path}:{query_string}"
    
    def configure_route_cache(self, path: str, duration: int) -> None:
        """
        Configure caching for a specific route.
        
        Args:
            path: Route path
            duration: Cache duration in seconds
        """
        self.cache_config[path] = duration
    
    def clear_cache(self, path: Optional[str] = None) -> None:
        """
        Clear cache for a specific route or all routes.
        
        Args:
            path: Route path, or None to clear all caches
        """
        try:
            if not self.redis_client.ping():
                print("Warning: Redis client is not connected, skipping cache clear.")
                return
            if path:
                # Clear cache for specific route
                pattern = f"cache:{path}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Clear all caches
                pattern = "cache:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache clear error: {e}")

