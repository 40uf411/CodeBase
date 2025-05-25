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
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        return user

    def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user, hashing their password.
        Only IntegrityError on email‐uniqueness is caught; other errors propagate.
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
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # Only translate unique‐email violations into our 400
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # On success, load defaults/PK
        self.db.refresh(user)
        return user

    def get_or_create_oauth_user(
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
            self.db.flush()
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
        self.db.commit()
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
        return self.create_tokens(user.id)

    def get_current_user(self, token: str) -> User:
        if is_token_revoked(token):
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

    def logout(self, token: str, refresh_token: str) -> None:
        revoke_token(token)
        revoke_token(refresh_token)

    def link_oauth_account(self, user_id: UUID, oauth_in: OAuthAccountCreate) -> OAuthAccount:
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
        self.db.commit()
        return acct

    def unlink_oauth_account(self, user_id: UUID, provider: str) -> None:
        acct = self.db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        ).first()
        if not acct:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="OAuth account not found")
        self.db.delete(acct)
        self.db.commit()
