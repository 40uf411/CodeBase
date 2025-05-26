from typing import List, Dict, Any, Optional
from uuid import UUID
# from fastapi import Depends # Removed Depends
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from models.sample import Sample
# from core.database import get_db # Removed get_db


class SampleRepository(BaseRepository[Sample]):
    """
    Repository for Sample model operations.
    """
    
    def __init__(self, db: Session): # Removed Depends(get_db)
        super().__init__(Sample, db)
    
    def get_by_name(self, name: str) -> Optional[Sample]:
        """
        Get a sample by name.
        
        Args:
            name: Sample name
            
        Returns:
            Sample if found, None otherwise
        """
        return self.db.query(Sample).filter(
            Sample.name == name,
            Sample.is_deleted == False
        ).first()
    
    def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a sample with the given name exists.
        
        Args:
            name: Sample name
            exclude_id: Sample ID to exclude from the check
            
        Returns:
            True if name exists, False otherwise
        """
        query = self.db.query(Sample).filter(
            Sample.name == name,
            Sample.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(Sample.id != exclude_id)
        
        return query.first() is not None
    
    def get_active_samples(self, skip: int = 0, limit: int = 100) -> List[Sample]:
        """
        Get all active samples.
        
        Args:
            skip: Number of samples to skip
            limit: Maximum number of samples to return
            
        Returns:
            List of active samples
        """
        return self.db.query(Sample).filter(
            Sample.is_active == True,
            Sample.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_by_priority(self, priority: int, skip: int = 0, limit: int = 100) -> List[Sample]:
        """
        Get samples by priority.
        
        Args:
            priority: Priority level (1-5)
            skip: Number of samples to skip
            limit: Maximum number of samples to return
            
        Returns:
            List of samples with the specified priority
        """
        return self.db.query(Sample).filter(
            Sample.priority == priority,
            Sample.is_deleted == False
        ).offset(skip).limit(limit).all()
