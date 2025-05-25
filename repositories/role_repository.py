from typing import Optional, List
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from models.role import Role
from core.database import get_db


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role model operations.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(Role, db)
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """
        Get a role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role if found, None otherwise
        """
        return self.db.query(Role).filter(
            Role.name == name,
            Role.is_deleted == False
        ).first()
    
    def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a role with the given name exists.
        
        Args:
            name: Role name
            exclude_id: Role ID to exclude from the check
            
        Returns:
            True if name exists, False otherwise
        """
        query = self.db.query(Role).filter(
            Role.name == name,
            Role.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(Role.id != exclude_id)
        
        return query.first() is not None
