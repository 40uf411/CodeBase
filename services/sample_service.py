import logging
from typing import List, Dict
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database import get_db
from repositories.sample_repository import SampleRepository
from services.privilege_service import PrivilegeService
from models.sample import Sample
from schemas.sample import SampleCreate, SampleUpdate

logger = logging.getLogger(__name__)

class SampleService:
    """
    Service for Sample operations with validation, transactions, and logging.
    """
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.repo = SampleRepository(db)
        self.priv_svc = PrivilegeService(db)

    def get_sample(self, sample_id: UUID) -> Sample:
        sam = self.repo.get(sample_id)
        if not sam:
            logger.warning(f"Sample not found: {sample_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Sample not found")
        return sam

    def get_samples(self, skip: int = 0, limit: int = 100) -> List[Sample]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_active_samples(self, skip: int = 0, limit: int = 100) -> List[Sample]:
        return self.repo.get_active(skip=skip, limit=limit)

    def get_by_priority(self, priority: int, skip: int = 0, limit: int = 100) -> List[Sample]:
        if not (1 <= priority <= 5):
            logger.error(f"Invalid priority: {priority}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Priority must be between 1 and 5")
        return self.repo.get_by_priority(priority, skip=skip, limit=limit)

    def create_sample(self, sample_in: SampleCreate) -> Sample:
        try:
            with self.db.begin():
                sam = self.repo.create(sample_in.dict())
                # create CRUD privileges for this entity
                self.priv_svc.create_crud_privileges("sample")
            logger.info(f"Created sample {sam.id} with name '{sam.name}'")
            return sam
        except IntegrityError as e:
            logger.error(f"Integrity error creating sample: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Sample with this name already exists")

    def update_sample(self, sample_id: UUID, sample_in: SampleUpdate) -> Sample:
        sam = self.get_sample(sample_id)
        data = sample_in.dict(exclude_unset=True)
        if 'name' in data and data['name'] != sam.name:
            if self.repo.name_exists(data['name'], exclude_id=sample_id):
                logger.error(f"Duplicate sample name on update: {data['name']}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Sample with this name already exists")
        with self.db.begin():
            updated = self.repo.update(sample_id, data)
        logger.info(f"Updated sample {sample_id}")
        return updated

    def delete_sample(self, sample_id: UUID, hard_delete: bool = False) -> Sample:
        sam = self.get_sample(sample_id)
        with self.db.begin():
            deleted = self.repo.delete(sample_id, hard_delete)
        logger.info(f"Deleted sample {sample_id} (hard={hard_delete})")
        return deleted