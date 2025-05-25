from typing import List, Dict, Any, Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from functools import wraps

from services.auth_service import AuthService
from services.privilege_service import PrivilegeService
from core.database import get_db

def requires_auth(func: Callable) -> Callable:
    """
    Decorator for routes that require authentication.
    
    Usage:
    ```
    @router.get("/protected")
    @requires_auth
    async def protected_route(request: Request):
        # Access authenticated user with request.state.user
        return {"message": f"Hello, {request.state.user.email}!"}
    ```
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
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
            return await func(request, *args, **kwargs)
            
        except HTTPException as e:
            # Re-raise authentication exceptions
            raise e
        except Exception as e:
            # Handle other exceptions
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}",
            )
        finally:
            # Close database session
            db.close()
    
    return wrapper


def requires_privileges(required_privileges: List[str]):
    """
    Decorator for routes that require specific privileges.
    
    Usage:
    ```
    @router.post("/items")
    @requires_privileges(["item:create"])
    async def create_item(request: Request, item: ItemCreate):
        # Access authenticated user with request.state.user
        return {"message": "Item created"}
    ```
    
    Args:
        required_privileges: List of required privileges in format "entity:action"
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @requires_auth
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from request state (set by requires_auth)
            user = request.state.user
            
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
