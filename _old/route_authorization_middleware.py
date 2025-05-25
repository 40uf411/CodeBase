from typing import List, Dict, Any, Optional, Callable
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
import inspect
import functools

from core.database import get_db
from services.auth_service import AuthService
from services.privilege_service import PrivilegeService

class RouteAuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatically adding authorization checks to routes.
    
    Features:
    - Automatically checks if users are logged in
    - Verifies users have appropriate role-based privileges
    - Blocks unauthorized access with proper error responses
    """
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self._add_auth_to_routes(app)
    
    def _add_auth_to_routes(self, app: FastAPI) -> None:
        """
        Add authorization checks to all routes.
        
        Args:
            app: FastAPI application
        """
        for route in app.routes:
            if isinstance(route, APIRoute):
                # Skip routes that already have auth checks
                if self._has_auth_dependency(route):
                    continue
                
                # Skip public routes
                if self._is_public_route(route.path):
                    continue
                
                # Get entity and action from route
                entity, action = self._get_entity_action_from_route(route)
                if entity and action:
                    # Add auth check to route
                    self._add_auth_dependency(route, entity, action)
    
    def _has_auth_dependency(self, route: APIRoute) -> bool:
        """
        Check if a route already has an auth dependency.
        
        Args:
            route: API route
            
        Returns:
            True if route has auth dependency, False otherwise
        """
        for dependency in route.dependencies:
            if "auth" in str(dependency.dependency).lower():
                return True
        return False
    
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
    
    def _get_entity_action_from_route(self, route: APIRoute) -> tuple:
        """
        Get entity and action from route.
        
        Args:
            route: API route
            
        Returns:
            Tuple of (entity, action)
        """
        path_parts = route.path.strip("/").split("/")
        if len(path_parts) < 1:
            return None, None
        
        # Get entity from first part of path
        entity = path_parts[0]
        
        # Get action from HTTP method
        method_action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        
        # Get HTTP method
        for method in route.methods:
            if method in method_action_map:
                action = method_action_map[method]
                return entity, action
        
        return entity, None
    
    def _add_auth_dependency(self, route: APIRoute, entity: str, action: str) -> None:
        """
        Add auth dependency to route.
        
        Args:
            route: API route
            entity: Entity name
            action: Action type (read, create, update, delete)
        """
        # Create auth dependency
        async def check_auth(
            request: Request,
            db = Depends(get_db)
        ) -> None:
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
            
            # Authenticate user
            auth_service = AuthService(db)
            user = auth_service.get_current_user(token)
            
            # Store user in request state
            request.state.user = user
            
            # Skip privilege check for superusers
            if user.is_superuser:
                return
            
            # Check privilege
            privilege_service = PrivilegeService(db)
            if not privilege_service.check_user_has_privilege(user.id, entity, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required privilege: {entity}:{action}",
                )
        
        # Add dependency to route
        route.dependencies.append(Depends(check_auth))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Just pass through, actual auth is handled by route dependencies
        return await call_next(request)
