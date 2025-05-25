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
        try:
            priv = self.repo.create(data)
            self.db.commit()
            logger.info(f"Created privilege {priv.name} (id={priv.id})")
            return priv
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error on creating privilege: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Privilege with this name already exists")

    def create_crud_privileges(self, entity: str) -> List[Privilege]:
        # Delegate to repository, which may handle its own commits
        try:
            privileges = self.repo.create_crud_privileges(entity)
            logger.info(f"CRUD privileges created for entity '{entity}'")
            return privileges
        except Exception as e:
            logger.error(f"Error creating CRUD privileges for {entity}: {e}")
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Could not create CRUD privileges")

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
                self.db.add(priv)
                self.db.commit()
            logger.info(f"Assigned privilege {priv.id} to role {role.id}")
            return priv
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error assigning privilege to role: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Could not assign privilege to role")

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
                self.db.add(priv)
                self.db.commit()
            logger.info(f"Removed privilege {priv.id} from role {role.id}")
            return priv
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error removing privilege from role: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Could not remove privilege from role")