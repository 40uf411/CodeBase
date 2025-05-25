from typing import Dict, List, Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from functools import wraps

from core.database import get_db
from services.auth_service import AuthService
from services.privilege_service import PrivilegeService

class AuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for checking user authorization.
    
    Features:
    - Authentication verification
    - Role-based access control
    - Permission checking for routes
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for public routes
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Get database session
        db = next(get_db())
        
        try:
            # Authenticate user
            auth_service = AuthService(db)
            user = auth_service.get_current_user(token)
            
            # Store user in request state
            request.state.user = user
            
            # Continue with request
            return await call_next(request)
            
        except HTTPException as e:
            # Re-raise authentication exceptions
            raise e
        except Exception as e:
            # Handle other exceptions
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authorization error: {str(e)}",
            )
        finally:
            # Close database session
            db.close()
    
    def _is_public_route(self, path: str) -> bool:
        """
        Check if a route is public (no authentication required).
        
        Args:
            path: Route path
            
        Returns:
            True if route is public, False otherwise
        """
        public_routes = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/google/login",
            "/auth/google/auth",
        ]
        
        # Check if path starts with any public route
        for route in public_routes:
            if path.startswith(route):
                return True
        
        return False


def check_privileges(required_privileges: List[str]):
    """
    Decorator for checking if user has required privileges.
    
    Args:
        required_privileges: List of required privileges
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Skip privilege check for superusers
            if user.is_superuser:
                return await func(request, *args, **kwargs)
            
            # Get database session
            db = next(get_db())
            
            try:
                # Check privileges
                privilege_service = PrivilegeService(db)
                
                # Check each required privilege
                for privilege in required_privileges:
                    entity, action = privilege.split(":")
                    if not privilege_service.check_user_has_privilege(user.id, entity, action):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not enough permissions. Missing privilege: {privilege}",
                        )
                
                # User has all required privileges
                return await func(request, *args, **kwargs)
                
            finally:
                # Close database session
                db.close()
                
        return wrapper
    return decorator
