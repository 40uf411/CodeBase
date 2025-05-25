from typing import List, Optional, TypeVar, Generic, Dict, Any
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime

from .base_repository import BaseRepository
from models.tt import TT
from core.database import get_db


T = TypeVar('T', bound=TT)

class TTRepository(BaseRepository[TT]):
    """
    Repository for TT model operations.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(TT, db)
    
    def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[TT]:
        """
        Get a tt by ID.
        
        Args:
            id: TT UUID
            include_deleted: Whether to include soft-deleted items
            
        Returns:
            TT if found, None otherwise
        """
        query = self.db.query(TT).filter(TT.id == id)
        
        if not include_deleted:
            query = query.filter(TT.is_deleted == False)
            
        return query.first()
    
    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[TT]:
        """
        Get all tts.
        
        Args:
            skip: Number of tts to skip
            limit: Maximum number of tts to return
            include_deleted: Whether to include soft-deleted items
            
        Returns:
            List of TTs
        """
        query = self.db.query(TT)
        
        if not include_deleted:
            query = query.filter(TT.is_deleted == False)
            
        return query.offset(skip).limit(limit).all()
    
    
    
    
    
    def create(self, obj_in: Dict[str, Any]) -> TT:
        """
        Create a new tt.
        
        Args:
            obj_in: TT data
            
        Returns:
            Created TT
        """
        db_obj = TT(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[TT]:
        """
        Update a tt.
        
        Args:
            id: TT UUID
            obj_in: TT data to update
            
        Returns:
            Updated TT if found, None otherwise
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
            
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
            
        # Update the updated_at timestamp
        db_obj.updated_at = datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: UUID, hard_delete: bool = False) -> Optional[TT]:
        """
        Delete a tt.
        
        Args:
            id: TT UUID
            hard_delete: Whether to permanently delete the tt
            
        Returns:
            Deleted TT if found, None otherwise
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
            
        if hard_delete:
            self.db.delete(db_obj)
        else:
            # Soft delete
            db_obj.soft_delete()
            
        self.db.commit()
        
        if not hard_delete:
            self.db.refresh(db_obj)
            
        return db_obj
    
    def restore(self, id: UUID) -> Optional[TT]:
        """
        Restore a soft-deleted tt.
        
        Args:
            id: TT UUID
            
        Returns:
            Restored TT if found, None otherwise
        """
        # Include deleted items in search
        db_obj = self.get_by_id(id, include_deleted=True)
        if not db_obj or not db_obj.is_deleted:
            return None
            
        db_obj.restore()
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj