from fastapi import Depends, HTTPException, status
from typing import Callable

from core.config import settings
from core.database import get_db
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .security import oauth2_scheme, get_current_user as _get_current_user, revoke_token, is_token_revoked, generate_password
from services.auth_service import AuthService
from services.privilege_service import PrivilegeService
from models.user import User


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_privilege_service(db: Session = Depends(get_db)) -> PrivilegeService:
    return PrivilegeService(db)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    return auth_service.get_current_user(token)


def require_privileges(*privileges: str) -> Callable:
    async def _dep(
        current_user: User = Depends(get_current_user),  # Awaited properly
        privilege_service: PrivilegeService = Depends(get_privilege_service),
    ):
        if current_user.is_superuser:
            return
        missing = [
            p for p in privileges
            if not privilege_service.check_user_has_privilege(current_user.id, *p.split(':'))
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing privileges: {', '.join(missing)}"
            )
    return Depends(_dep)