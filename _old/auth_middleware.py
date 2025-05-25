from typing import Optional, List
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError

from core.config import settings
from core.database import get_db
from services.auth_service import AuthService
from repositories.privilege_repository import PrivilegeRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.PROJECT_VER_STR}/auth/login")

class AuthMiddleware:
    """
    Middleware for authentication and authorization.
    
    Features:
    - JWT token validation
    - User authentication
    - Role-based access control
    - Permission checking
    """
    
    @staticmethod
    async def authenticate_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Authenticate user from JWT token.
        
        Args:
            request: FastAPI request
            token: JWT token
            db: Database session
            
        Returns:
            User object if authenticated
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            auth_service = AuthService(db)
            user = auth_service.get_current_user(token)
            request.state.user = user
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def check_permissions(request: Request, required_privileges: List[str], db: Session = Depends(get_db)):
        """
        Check if user has required privileges.
        
        Args:
            request: FastAPI request
            required_privileges: List of required privileges
            db: Database session
            
        Returns:
            True if user has required privileges
            
        Raises:
            HTTPException: If user doesn't have required privileges
        """
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Superusers have all privileges
        if user.is_superuser:
            return True
        
        # Check user privileges
        privilege_repo = PrivilegeRepository(db)
        user_privileges = privilege_repo.get_user_privileges(user.id)
        
        # Check if user has any of the required privileges
        for privilege in required_privileges:
            if privilege in user_privileges:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


def requires_auth(func):
    """
    Decorator for routes that require authentication.
    """
    async def wrapper(request: Request, *args, **kwargs):
        await AuthMiddleware.authenticate_user(request)
        return await func(request, *args, **kwargs)
    return wrapper


def requires_privileges(privileges: List[str]):
    """
    Decorator for routes that require specific privileges.
    
    Args:
        privileges: List of required privileges
    """
    def decorator(func):
        async def wrapper(request: Request, db: Session = Depends(get_db), *args, **kwargs):
            await AuthMiddleware.authenticate_user(request)
            await AuthMiddleware.check_permissions(request, privileges, db)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
