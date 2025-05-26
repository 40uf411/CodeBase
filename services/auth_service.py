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
        try:
            # Check if OAuth account already exists
            acct = self.db.query(OAuthAccount).filter(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            ).first()

            if acct:
                # Update existing OAuth account tokens if new ones are provided
                if access_token: acct.access_token = access_token
                if refresh_token: acct.refresh_token = refresh_token
                if expires_at: acct.expires_at = expires_at
                # self.db.add(acct) # Not strictly necessary if already in session and modified
                self.db.commit() # Commit changes to existing OAuth account
                self.db.refresh(acct)
                logger.info(f"Updated OAuthAccount {provider}:{provider_user_id}")
                return acct.user # Return associated user

            # OAuth account does not exist, try to find user by email
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                # Create new user if not found
                user = User(
                    email=email,
                    hashed_password=None, # OAuth users might not have a local password initially
                    full_name=full_name,
                    is_active=True,
                    is_superuser=False,
                )
                self.db.add(user)
                # We need user.id for OAuthAccount, flush to get it before creating OAuthAccount
                self.db.flush() 
                logger.info(f"Created new user {email} for OAuth.")
            
            # Create new OAuthAccount and link to user
            new_acct = OAuthAccount(
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                user_id=user.id  # Link to existing or newly created user
            )
            self.db.add(new_acct)
            self.db.commit() # Commit new user (if any) and new OAuth account
            self.db.refresh(user)
            if new_acct in self.db: self.db.refresh(new_acct) # Check if new_acct is in session before refreshing
            logger.info(f"Linked OAuthAccount {provider}:{provider_user_id} to user {user.id}")
            return user
        except IntegrityError as e: # Catch potential unique constraint violations, etc.
            self.db.rollback()
            logger.error(f"IntegrityError in get_or_create_oauth_user: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth user processing failed due to data conflict.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Exception in get_or_create_oauth_user: {e}")
            # Consider raising a more generic error or re-raising specific non-HTTPException
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during OAuth user processing.")

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
        acct_model = OAuthAccount(**oauth_in.dict())
        acct_model.user_id = user_id
        self.db.add(acct_model)
        try:
            self.db.commit()
            self.db.refresh(acct_model)
            return acct_model
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to link OAuth account due to integrity error: {e}")
            # Check if it's a duplicate linking attempt that wasn't caught by the initial check
            # This specific error might indicate a race condition or a subtle bug if the initial check passed.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="OAuth account could not be linked, possibly already exists or data conflict.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error linking OAuth account: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not link OAuth account due to an unexpected error.")


    async def unlink_oauth_account(self, user_id: UUID, provider: str) -> None: # Made async
        acct = self.db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        ).first() # Sync call
        if not acct:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="OAuth account not found")
        self.db.delete(acct) # Sync call
        try:
            self.db.commit() # Sync call
        except Exception as e: # Catch potential errors during commit, though less common for delete
            self.db.rollback()
            logger.error(f"Error unlinking OAuth account: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not unlink OAuth account due to an unexpected error.")
