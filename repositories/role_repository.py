from typing import Optional, List
from uuid import UUID
from sqlalchemy import select # Added
from sqlalchemy.ext.asyncio import AsyncSession # Added

from .base_repository import BaseRepository
from models.role import Role


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role model operations, adapted for asynchronous operations.
    """
    
    def __init__(self, db: AsyncSession): # Updated to AsyncSession
        super().__init__(Role, db) # Pass AsyncSession to base
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """
        Get a role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role if found, None otherwise
        """
        query = select(Role).filter(
            Role.name == name,
            Role.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a role with the given name exists.
        
        Args:
            name: Role name
            exclude_id: Role ID to exclude from the check
            
        Returns:
            True if name exists, False otherwise
        """
        query = select(Role.id).filter( # Optimized to select only ID
            Role.name == name,
            Role.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(Role.id != exclude_id)
        
        result = await self.db.execute(query)
        return result.first() is not None

# Dependency provider function
from fastapi import Depends
from core.database import get_async_db # Updated to get_async_db

def get_role_repository(db: AsyncSession = Depends(get_async_db)) -> RoleRepository: # Updated to AsyncSession
    return RoleRepository(db)
