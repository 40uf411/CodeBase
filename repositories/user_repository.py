from typing import Optional, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from models.user import User
from core.database import get_db


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(
            User.email == email,
            User.is_deleted == False
        ).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        return self.db.query(User).filter(
            User.is_active == True,
            User.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_superusers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all superusers.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of superusers
        """
        return self.db.query(User).filter(
            User.is_superuser == True,
            User.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a user with the given email exists.
        
        Args:
            email: User email
            exclude_id: User ID to exclude from the check
            
        Returns:
            True if email exists, False otherwise
        """
        query = self.db.query(User).filter(
            User.email == email,
            User.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        
        return query.first() is not None
