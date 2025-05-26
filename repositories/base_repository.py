from typing import Generic, TypeVar, List, Optional, Dict, Any, Type
from uuid import UUID
from sqlalchemy import select, func # Added
from sqlalchemy.ext.asyncio import AsyncSession # Added

from core.exceptions import EntityNotFoundError # Added (already present)
from models.base import BaseModel

# Type variable for generic repository
T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository with generic CRUD operations, adapted for asynchronous operations.
    """
    
    def __init__(self, model: Type[T], db: AsyncSession): # Updated to AsyncSession
        self.model = model
        self.db = db
    
    async def get(self, id: UUID) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        # Using db.get for direct primary key lookup is efficient.
        # The is_deleted check is then performed on the retrieved object.
        obj = await self.db.get(self.model, id)
        if obj and obj.is_deleted:
            return None
        return obj
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        query = select(self.model).filter(
            self.model.is_deleted == False
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """
        Create a new record.
        
        Args:
            obj_in: Record creation data
            
        Returns:
            Created record
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[T]:
        """
        Update a record.
        
        Args:
            id: Record ID
            obj_in: Record update data
            
        Returns:
            Updated record or None if not found.
        """
        db_obj = await self.get(id) # get() is now async and handles is_deleted
        if not db_obj:
            return None 
        
        # Update fields
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and field != "id": # Ensure 'id' is not accidentally changed
                setattr(db_obj, field, value)
        
        self.db.add(db_obj) # Add the existing, modified object to the session
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID, hard_delete: bool = False) -> Optional[T]:
        """
        Delete a record.
        
        Args:
            id: Record ID
            hard_delete: Whether to permanently delete the record
            
        Returns:
            Deleted record or None if not found.
        """
        db_obj = await self.get(id) # get() is now async and handles is_deleted
        if not db_obj:
            return None
        
        if hard_delete:
            await self.db.delete(db_obj)
            await self.db.flush()
        else:
            db_obj.soft_delete() # This method should set is_deleted = True, updated_at
            self.db.add(db_obj)
            await self.db.flush()
            await self.db.refresh(db_obj) # Refresh to get updated state like updated_at
        return db_obj # Return the object (even if hard-deleted, it was the state before deletion)
    
    async def count(self) -> int:
        """
        Count all non-deleted records.
        
        Returns:
            Number of records
        """
        query = select(func.count(self.model.id)).select_from(self.model).filter(
            self.model.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists (and is not soft-deleted).
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists and is not soft-deleted, False otherwise
        """
        # Optimized to only fetch the ID, reducing data transfer.
        query = select(self.model.id).filter(
            self.model.id == id,
            self.model.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.first() is not None
