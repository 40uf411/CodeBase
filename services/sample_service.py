import logging
from typing import List, Dict
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request # Added Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from utils.activity_logging_decorators import log_activity # Added decorator

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
        self.priv_svc = PrivilegeService(db) # Assuming this is synchronous for now

    async def get_sample(self, sample_id: UUID, request: Request = None) -> Sample: # Made async, added request
        # This method is not specified for decoration, but making it async for consistency if other methods call it.
        # The request param is added for potential future decoration or use by called decorated methods.
        sam = self.repo.get(sample_id) # Sync call
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
        return self.repo.get_by_priority(priority, skip=skip, limit=limit) # Sync call

    @log_activity(success_event_type="SAMPLE_CREATE_SUCCESS", failure_event_type="SAMPLE_CREATE_FAILURE")
    async def create_sample(self, sample_in: SampleCreate, request: Request = None) -> Sample: # Made async, added request
        try:
            # Synchronous DB operations within the async method
            with self.db.begin(): # Sync context manager
                sam = self.repo.create(sample_in.dict()) # Sync call
                # create CRUD privileges for this entity
                self.priv_svc.create_crud_privileges("sample") # Sync call
            # logger.info(f"Created sample {sam.id} with name '{sam.name}'") # Logging now handled by decorator
            return sam
        except IntegrityError as e:
            # logger.error(f"Integrity error creating sample: {e}") # Logging now handled by decorator on failure
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Sample with this name already exists")

    @log_activity(success_event_type="SAMPLE_UPDATE_SUCCESS", failure_event_type="SAMPLE_UPDATE_FAILURE")
    async def update_sample(self, sample_id: UUID, sample_in: SampleUpdate, request: Request = None) -> Sample: # Made async, added request
        sam = await self.get_sample(sample_id, request=request) # Now async, ensure it's awaited if it becomes truly async
        data = sample_in.dict(exclude_unset=True)
        if 'name' in data and data['name'] != sam.name:
            if self.repo.name_exists(data['name'], exclude_id=sample_id): # Sync call
                # logger.error(f"Duplicate sample name on update: {data['name']}") # Logging by decorator
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Sample with this name already exists")
        with self.db.begin(): # Sync context manager
            updated = self.repo.update(sample_id, data) # Sync call
        # logger.info(f"Updated sample {sample_id}") # Logging by decorator
        return updated

    async def delete_sample(self, sample_id: UUID, hard_delete: bool = False, request: Request = None) -> Sample: # Made async, added request
        # This method is not specified for decoration in this PoC
        sam = await self.get_sample(sample_id, request=request) # Now async
        with self.db.begin(): # Sync context manager
            deleted = self.repo.delete(sample_id, hard_delete) # Sync call
        logger.info(f"Deleted sample {sample_id} (hard={hard_delete})") # Standard logger, not activity log here
        return deleted