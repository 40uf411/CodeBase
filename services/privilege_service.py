import logging
from typing import List, Dict, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database import get_db
from repositories.privilege_repository import PrivilegeRepository
from repositories.role_repository import RoleRepository
# from services.privilege_service import PrivilegeService  # For nested calls
from models.privilege import Privilege

logger = logging.getLogger(__name__)

class PrivilegeService:
    """
    Service for Privilege operations with transactional safety and logging.
    """
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.repo = PrivilegeRepository(db)

    def get_privilege(self, privilege_id: UUID) -> Privilege:
        priv = self.repo.get(privilege_id)
        if not priv:
            logger.warning(f"Privilege not found: {privilege_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Privilege not found")
        return priv

    def get_privileges(self, skip: int = 0, limit: int = 100) -> List[Privilege]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_privileges_by_entity(self, entity: str) -> List[Privilege]:
        return self.repo.get_by_entity(entity)

    def create_privilege(self, data: Dict[str, Any]) -> Privilege:
        # repo.create now only adds to session and refreshes. Service must commit.
        priv = self.repo.create(data) 
        try:
            self.db.commit()
            self.db.refresh(priv) # Ensure all DB-generated values are loaded after commit
            logger.info(f"Created privilege {priv.name} (id={priv.id})")
            return priv
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error on creating privilege: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Privilege with this name already exists or other integrity violation.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating privilege: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create privilege.")


    def create_crud_privileges(self, entity: str) -> List[Privilege]:
        # repo.create_crud_privileges now only adds to session. Service must commit.
        privileges = self.repo.create_crud_privileges(entity)
        try:
            self.db.commit()
            for p in privileges: # Refresh each privilege to get DB defaults if they were newly created
                if p in self.db: # Check if object is still in session (it should be)
                    self.db.refresh(p)
            logger.info(f"CRUD privileges created/verified for entity '{entity}'")
            return privileges
        except Exception as e: # Catch any exception during commit
            self.db.rollback()
            logger.error(f"Error committing CRUD privileges for {entity}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Could not create/commit CRUD privileges")

    def assign_privilege_to_role(self, privilege_id: UUID, role_id: UUID) -> Privilege:
        priv = self.get_privilege(privilege_id)
        role = RoleRepository(self.db).get(role_id)
        if not role:
            logger.warning(f"Role not found: {role_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Role not found")
        try:
            if role not in priv.roles:
                priv.roles.append(role)
                self.db.add(priv) # Mark the privilege object as dirty due to relationship change
                self.db.commit()
                self.db.refresh(priv) # Refresh to get updated state if needed (e.g. version_id)
            logger.info(f"Assigned privilege {priv.id} to role {role.id}")
            return priv
        except IntegrityError as e: # This might occur for various reasons depending on DB schema
            self.db.rollback()
            logger.error(f"Integrity error assigning privilege to role: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Could not assign privilege to role due to data integrity issue.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error assigning privilege to role: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not assign privilege to role.")


    def remove_privilege_from_role(self, privilege_id: UUID, role_id: UUID) -> Privilege:
        priv = self.get_privilege(privilege_id)
        role = RoleRepository(self.db).get(role_id)
        if not role:
            logger.warning(f"Role not found: {role_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Role not found")
        try:
            if role in priv.roles:
                priv.roles.remove(role)
                self.db.add(priv) # Mark the privilege object as dirty
                self.db.commit()
                self.db.refresh(priv) # Refresh to get updated state
            logger.info(f"Removed privilege {priv.id} from role {role.id}")
            return priv
        except Exception as e: # Catch general exceptions during commit/DB operation
            self.db.rollback()
            logger.error(f"Error removing privilege from role: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not remove privilege from role.")

# Dependency provider function
def get_privilege_service(db: Session = Depends(get_db)) -> PrivilegeService:
    return PrivilegeService(db)