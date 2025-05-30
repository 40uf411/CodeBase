from typing import Optional, List
from uuid import UUID
from sqlalchemy import select # Added
from sqlalchemy.ext.asyncio import AsyncSession # Added

from .base_repository import BaseRepository
from models.user import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations, adapted for asynchronous operations.
    """
    
    def __init__(self, db: AsyncSession): # Updated to AsyncSession
        super().__init__(User, db) # Pass AsyncSession to base
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        query = select(User).filter(
            User.email == email,
            User.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of active users
        """
        query = select(User).filter(
            User.is_active == True,
            User.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_superusers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all superusers.
        
        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of superusers
        """
        query = select(User).filter(
            User.is_superuser == True,
            User.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a user with the given email exists.
        
        Args:
            email: User email
            exclude_id: User ID to exclude from the check
            
        Returns:
            True if email exists, False otherwise
        """
        query = select(User.id).filter( # Optimized to select only ID
            User.email == email,
            User.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.first() is not None

# Dependency provider function
from fastapi import Depends
from core.database import get_async_db # Updated to get_async_db

def get_user_repository(db: AsyncSession = Depends(get_async_db)) -> UserRepository: # Updated to AsyncSession
    return UserRepository(db)
