from typing import Generic, TypeVar, List, Optional, Dict, Any, Type
from uuid import UUID
from fastapi import HTTPException, status 
from sqlalchemy.orm import Session

from core.exceptions import EntityNotFoundError # Added
from models.base import BaseModel

# Type variable for generic repository
T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository with generic CRUD operations.
    """
    
    def __init__(self, model: Type[T], db: Session): # Removed Depends(get_db)
        self.model = model
        self.db = db
    
    def get(self, id: UUID) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        return self.db.query(self.model).filter(
            self.model.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> T:
        """
        Create a new record.
        
        Args:
            obj_in: Record creation data
            
        Returns:
            Created record
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        # self.db.commit() # Removed commit
        self.db.refresh(db_obj) # Keep refresh for ID/defaults
        return db_obj
    
    def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[T]: # Changed return type
        """
        Update a record.
        
        Args:
            id: Record ID
            obj_in: Record update data
            
        Returns:
            Updated record or None if not found.
        """
        db_obj = self.get(id) # get() already returns Optional[T]
        if not db_obj:
            return None # Return None if entity not found
        
        # Update fields
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and field != "id":
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        # self.db.commit() # Removed commit
        self.db.refresh(db_obj) # Keep refresh
        return db_obj
    
    def delete(self, id: UUID, hard_delete: bool = False) -> Optional[T]: # Changed return type
        """
        Delete a record.
        
        Args:
            id: Record ID
            hard_delete: Whether to permanently delete the record
            
        Returns:
            Deleted record or None if not found.
        """
        db_obj = self.get(id) # get() already returns Optional[T]
        if not db_obj:
            return None # Return None if entity not found
        
        if hard_delete:
            self.db.delete(db_obj)
        else:
            db_obj.soft_delete()
            self.db.add(db_obj)
        
        # self.db.commit() # Removed commit
        # For soft delete, the object `db_obj` is already updated in memory.
        # Refresh after commit is the service's responsibility if it needs a fully updated state from DB.
        # For hard delete, the object is gone from session after commit.
        return db_obj
    
    def count(self) -> int:
        """
        Count all non-deleted records.
        
        Returns:
            Number of records
        """
        return self.db.query(self.model).filter(
            self.model.is_deleted == False
        ).count()
    
    def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).first() is not None
