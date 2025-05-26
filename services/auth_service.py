import logging
from typing import Optional, Dict
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import jwt, JWTError

from core.config import settings
from core.database import get_db
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, is_token_revoked, revoke_token
from models.user import User
from models.oauth_account import OAuthAccount
from schemas.user import UserCreate
from schemas.oauth_account import OAuthAccountCreate
from sqlalchemy.exc import IntegrityError
from fastapi import Request # Added for request parameter
from utils.activity_logging_decorators import log_activity # Added decorator

logger = logging.getLogger(__name__)

class AuthService:
    # Added request to __init__ for explicit logging example in authenticate_user
    def __init__(self, db: Session = Depends(get_db), request: Request = None):
        self.db = db
        self.request = request # Store request if provided

    def authenticate_user(self, email: str, password: str) -> User:
        logger_service = None
        if self.request and hasattr(self.request.app.state, "activity_logger_service"):
            logger_service = self.request.app.state.activity_logger_service
        
        log_details_base = {
            "email_attempted": email, 
            "target_resource_type": "USER",
            "function_name": "authenticate_user", # Manual addition for context
            "module_name": self.__module__ # Manual addition for context
        }

        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            if logger_service:
                log_event = {
                    "event_type": "USER_LOGIN_FAILURE", 
                    **log_details_base,
                    "failure_reason": "Incorrect email or password"
                }
                logger_service.log(log_event)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        
        if logger_service:
            log_event = {
                "event_type": "USER_LOGIN_SUCCESS",
                **log_details_base,
                "target_resource_ids": [str(user.id)], # Use list for consistency
                "actor_user_email": user.email # For login, actor is the user logging in
            }
            logger_service.log(log_event)
        return user

    @log_activity(success_event_type="USER_CREATE_SUCCESS", failure_event_type="USER_CREATE_FAILURE")
    async def create_user(self, user_in: UserCreate, request: Request = None) -> User: # Added request: Request = None, made async
        """
        Create a new user, hashing their password.
        Only IntegrityError on email‐uniqueness is caught; other errors propagate.
        The 'request' parameter is for the log_activity decorator.
        """
        hashed = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            hashed_password=hashed,
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
        )
        self.db.add(user)
        try:
            self.db.commit() # SQLAlchemy sessions are typically not async for commit unless using async extension
            self.db.refresh(user) # Same here
        except IntegrityError as e:
            self.db.rollback()
            # Only translate unique‐email violations into our 400
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # On success, load defaults/PK
        # self.db.refresh(user) # Already done above
        return user

    async def get_or_create_oauth_user( # Made async to align if other methods become async
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        full_name: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> User:
        acct = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        ).first()
        if acct:
            # Assuming self.db.begin() is for synchronous session, if it's part of an async setup, needs adjustment
            with self.db.begin(): 
                if access_token:
                    acct.access_token = access_token
                if refresh_token:
                    acct.refresh_token = refresh_token
                if expires_at:
                    acct.expires_at = expires_at
            logger.info(f"Updated OAuthAccount {provider}:{provider_user_id}")
            return acct.user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=None,
                full_name=full_name,
                is_active=True,
                is_superuser=False,
            )
            self.db.add(user)
            self.db.flush() # Sync call
            logger.info(f"Created OAuth user {email}")
        acct = OAuthAccount(
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_id=user.id
        )
        self.db.add(acct)
        self.db.commit() # Sync call
        logger.info(f"Linked OAuthAccount {provider}:{provider_user_id} to user {user.id}")
        return user

    def create_tokens(self, user_id: UUID) -> Dict[str, str]:
        access_expires = timedelta(minutes=settings.JWT_EXPIRATION)
        access = create_access_token(subject=str(user_id), expires_delta=access_expires)
        refresh = create_refresh_token(subject=str(user_id))
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    def refresh_token(self, token: str) -> Dict[str, str]:
        if is_token_revoked(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Refresh token revoked")
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            sub = payload.get("sub")
            typ = payload.get("type")
            if typ != "refresh" or sub is None:
                raise JWTError()
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid refresh token")
        user = self.db.query(User).filter(User.id == sub).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="User not found or inactive")
        return self.create_tokens(user.id) # This returns a dict, not an awaitable

    async def get_current_user(self, token: str) -> User: # Made async
        if is_token_revoked(token): # Assuming is_token_revoked is sync
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token revoked")
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            sub = payload.get("sub")
            if sub is None:
                raise JWTError()
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        user = self.db.query(User).filter(User.id == sub).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")
        return user

    async def logout(self, token: str, refresh_token: str) -> None: # Made async
        revoke_token(token) # Assuming revoke_token is sync
        revoke_token(refresh_token) # Assuming revoke_token is sync

    async def link_oauth_account(self, user_id: UUID, oauth_in: OAuthAccountCreate) -> OAuthAccount: # Made async
        existing = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == oauth_in.provider,
            OAuthAccount.provider_user_id == oauth_in.provider_user_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="OAuth account already linked")
        acct = OAuthAccount(**oauth_in.dict())
        acct.user_id = user_id
        self.db.add(acct)
        self.db.commit() # Sync call
        return acct

    async def unlink_oauth_account(self, user_id: UUID, provider: str) -> None: # Made async
        acct = self.db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        ).first() # Sync call
        if not acct:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="OAuth account not found")
        self.db.delete(acct) # Sync call
        self.db.commit() # Sync call
