from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_ # Added select
from sqlalchemy.ext.asyncio import AsyncSession # Added
from sqlalchemy.orm import selectinload # Added for eager loading

from .base_repository import BaseRepository
from models.privilege import Privilege
from models.user import User # Added for type hint in get_user_privileges
from models.role import Role


class PrivilegeRepository(BaseRepository[Privilege]):
    """
    Repository for Privilege model operations, adapted for asynchronous operations.
    """
    
    def __init__(self, db: AsyncSession): # Updated to AsyncSession
        super().__init__(Privilege, db) # Pass AsyncSession to base
    
    async def get_by_name(self, name: str) -> Optional[Privilege]:
        """
        Get a privilege by name.
        
        Args:
            name: Privilege name
            
        Returns:
            Privilege if found, None otherwise
        """
        query = select(Privilege).filter(
            Privilege.name == name,
            Privilege.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_entity_and_action(self, entity: str, action: str) -> Optional[Privilege]:
        """
        Get a privilege by entity and action.
        
        Args:
            entity: Entity name
            action: Action type (read, write, update, delete)
            
        Returns:
            Privilege if found, None otherwise
        """
        query = select(Privilege).filter(
            Privilege.entity == entity,
            Privilege.action == action,
            Privilege.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_entity(self, entity: str) -> List[Privilege]:
        """
        Get all privileges for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of privileges
        """
        query = select(Privilege).filter(
            Privilege.entity == entity,
            Privilege.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_privileges(self, user_id: UUID) -> List[str]:
        """
        Get all privilege names for a user through their roles.
        
        Args:
            user_id: User ID
            
        Returns:
            List of privilege names
        """
        # Eagerly load roles and their privileges for the user
        user_query = select(User).options(
            selectinload(User.roles).selectinload(Role.privileges)
        ).filter(User.id == user_id, User.is_deleted == False)
        
        user_result = await self.db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            return []

        privilege_names = set()
        for role in user.roles:
            if not role.is_deleted:
                for privilege in role.privileges:
                    if not privilege.is_deleted:
                        privilege_names.add(privilege.name)
        
        return list(privilege_names)
    
    async def create_crud_privileges(self, entity: str) -> List[Privilege]:
        """
        Create CRUD privileges for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of created privileges
        """
        actions = {
            "read": f"Read {entity}",
            "create": f"Create {entity}",
            "update": f"Update {entity}",
            "delete": f"Delete {entity}"
        }
        
        created_privileges = []
        
        for action, description in actions.items():
            privilege = await self.get_by_entity_and_action(entity, action)
            
            if not privilege:
                privilege_name = f"{entity.lower()}:{action}"
                new_privilege = Privilege(
                    name=privilege_name,
                    description=description,
                    entity=entity,
                    action=action
                )
                
                self.db.add(new_privilege)
                await self.db.flush()
                await self.db.refresh(new_privilege)
                created_privileges.append(new_privilege)
            else:
                created_privileges.append(privilege) # Append existing if found
        
        return created_privileges

# Dependency provider function
from fastapi import Depends
from core.database import get_async_db

def get_privilege_repository(db: AsyncSession = Depends(get_async_db)) -> PrivilegeRepository:
    return PrivilegeRepository(db)
