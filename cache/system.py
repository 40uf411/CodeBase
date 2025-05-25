import json
import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
import redis

from core.config import settings


class CacheSystem:
    """
    Core caching logic using DragonFlyDB (Redis API).
    """
    def __init__(self, client: Optional[redis.Redis] = None):
        self.client = client or redis.Redis(
            host=settings.DRAGONFLY_HOST,
            port=settings.DRAGONFLY_PORT,
            db=settings.DRAGONFLY_DB,
            password=settings.DRAGONFLY_PASSWORD,
            decode_responses=False,
        )
        # route -> ttl
        self.config: dict[str, int] = {}

    def configure_route(self, path: str, ttl: int):
        """Enable caching on `path` for `ttl` seconds."""
        self.config[path] = ttl

    def get_ttl(self, path: str) -> Optional[int]:
        return self.config.get(path)

    def clear(self, path: Optional[str] = None):
        """Invalidate all or one path’s cache entries."""
        pattern = f"cache:{path or '*'}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

    def _make_key(self, path: str, params: str, user_id: Optional[str]) -> str:
        uid = user_id or "anon"
        return f"cache:{path}:{uid}:{params}"

    def get(self, key: str) -> Optional[bytes]:
        try:
            return self.client.get(key)
        except redis.exceptions.RedisError as e:
            print(f"Warning: Failed to read from DragonFlyDB: {e}")
            return None

    def set(self, key: str, data: bytes, ttl: int):
        try:
            if ttl > 0:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
        except redis.exceptions.RedisError as e:
            print(f"Warning: Failed to write to DragonFlyDB: {e}")



def cache_response(ttl: int):
    """
    Decorator to cache the JSON response of a GET endpoint.
    """
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Locate the Request object
            request: Optional[Request] = kwargs.get('request', None)
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            # If we don't have a Request, just call through
            if not request:
                return await fn(*args, **kwargs)

            sys: CacheSystem = request.app.state.cache_system
            path = request.url.path
            # Register TTL once
            if sys.get_ttl(path) is None:
                sys.configure_route(path, ttl)

            # Only cache GET requests
            if request.method != 'GET':
                return await fn(*args, **kwargs)

            # Build cache key
            params = '&'.join(sorted(request.query_params.multi_items()))
            user = getattr(request.state, 'user', None)
            user_id = getattr(user, 'id', None)
            key = sys._make_key(path, params, str(user_id) if user_id else None)

            # Try cache
            raw = sys.get(key)
            if raw:
                cached = json.loads(raw)
                return Response(
                    content=cached['body'],
                    status_code=cached['status_code'],
                    headers=cached['headers'],
                    media_type='application/json',
                )

            # Call the actual endpoint
            response: Response = await fn(*args, **kwargs)

            # Only cache successful JSON responses
            if 200 <= response.status_code < 300 and 'application/json' in response.media_type:
                body = b''
                async for chunk in response.body_iterator:
                    body += chunk
                payload = {
                    'body': body.decode(),
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                }
                sys.set(key, json.dumps(payload).encode(), ttl)
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type,
                )
            return response

        return wrapper
    return decorator
