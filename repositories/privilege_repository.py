from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base_repository import BaseRepository
from models.privilege import Privilege
from models.role import Role
from core.database import get_db


class PrivilegeRepository(BaseRepository[Privilege]):
    """
    Repository for Privilege model operations.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(Privilege, db)
    
    def get_by_name(self, name: str) -> Optional[Privilege]:
        """
        Get a privilege by name.
        
        Args:
            name: Privilege name
            
        Returns:
            Privilege if found, None otherwise
        """
        return self.db.query(Privilege).filter(
            Privilege.name == name,
            Privilege.is_deleted == False
        ).first()
    
    def get_by_entity_and_action(self, entity: str, action: str) -> Optional[Privilege]:
        """
        Get a privilege by entity and action.
        
        Args:
            entity: Entity name
            action: Action type (read, write, update, delete)
            
        Returns:
            Privilege if found, None otherwise
        """
        return self.db.query(Privilege).filter(
            Privilege.entity == entity,
            Privilege.action == action,
            Privilege.is_deleted == False
        ).first()
    
    def get_by_entity(self, entity: str) -> List[Privilege]:
        """
        Get all privileges for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of privileges
        """
        return self.db.query(Privilege).filter(
            Privilege.entity == entity,
            Privilege.is_deleted == False
        ).all()
    
    def get_user_privileges(self, user_id: UUID) -> List[str]:
        """
        Get all privilege names for a user through their roles.
        
        Args:
            user_id: User ID
            
        Returns:
            List of privilege names
        """
        # Get all roles for the user
        roles = self.db.query(Role).join(
            Role.users
        ).filter(
            and_(
                Role.users.any(id=user_id),
                Role.is_deleted == False
            )
        ).all()
        
        # Get all privileges for these roles
        privilege_names = set()
        for role in roles:
            for privilege in role.privileges:
                if not privilege.is_deleted:
                    privilege_names.add(privilege.name)
        
        return list(privilege_names)
    
    def create_crud_privileges(self, entity: str) -> List[Privilege]:
        """
        Create CRUD privileges for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of created privileges
        """
        # Define CRUD actions
        actions = {
            "read": f"Read {entity}",
            "create": f"Create {entity}",
            "update": f"Update {entity}",
            "delete": f"Delete {entity}"
        }
        
        created_privileges = []
        
        # Create privileges for each action
        for action, description in actions.items():
            # Check if privilege already exists
            privilege = self.get_by_entity_and_action(entity, action)
            
            if not privilege:
                # Create new privilege
                privilege_name = f"{entity.lower()}:{action}"
                privilege = Privilege(
                    name=privilege_name,
                    description=description,
                    entity=entity,
                    action=action
                )
                
                self.db.add(privilege)
                self.db.commit()
                self.db.refresh(privilege)
                
                created_privileges.append(privilege)
            else:
                created_privileges.append(privilege)
        
        return created_privileges
