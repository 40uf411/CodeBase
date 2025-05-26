from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, status, Request # Added Request
from sqlalchemy.orm import Session

from core.database import get_db
from utils.activity_logging_decorators import log_activity # Added
from core.auth import require_privileges
from services.sample_service import SampleService
from services.privilege_service import PrivilegeService
from schemas.sample import SampleResponse, SampleCreate, SampleUpdate

router = APIRouter(
    prefix="/samples",
    tags=["samples"],
    dependencies=[ require_privileges("sample:read") ],
)

@router.post(
    "/",
    response_model=SampleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ require_privileges("sample:create") ],
    summary="Create a new sample"
)
@log_activity(success_event_type="SAMPLE_CREATE_VIA_API_SUCCESS", failure_event_type="SAMPLE_CREATE_VIA_API_FAILURE")
async def create_sample(
    sample_in: SampleCreate,
    request: Request, # Added request
    db: Session = Depends(get_db),
):
    sample_service = SampleService(db)
    # SampleService.create_sample is now async and expects request
    sample = await sample_service.create_sample(sample_in, request=request)
    # ensure CRUD privileges exist
    # PrivilegeService(db).create_crud_privileges("sample") # This might also be a candidate for logging if made async
    return sample

@router.get(
    "/",
    response_model=List[SampleResponse],
    summary="List samples"
)
async def list_samples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return SampleService(db).get_samples(skip=skip, limit=limit)

@router.get(
    "/active",
    response_model=List[SampleResponse],
    summary="List active samples"
)
async def list_active_samples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return SampleService(db).get_active_samples(skip=skip, limit=limit)

@router.get(
    "/priority/{priority}",
    response_model=List[SampleResponse],
    summary="List samples by priority"
)
async def list_samples_by_priority(
    priority: int = Path(..., ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return SampleService(db).get_by_priority(priority, skip=skip, limit=limit)

@router.get(
    "/{sample_id}",
    response_model=SampleResponse,
    summary="Get a sample"
)
async def get_sample( # Renamed from get_sample to avoid conflict with service method name if we were to use it directly
    sample_id: UUID,
    request: Request, # Added request, though not decorating this endpoint in PoC
    db: Session = Depends(get_db),
):
    # SampleService.get_sample is now async and expects request
    return await SampleService(db).get_sample(sample_id, request=request)

@router.put(
    "/{sample_id}",
    response_model=SampleResponse,
    dependencies=[ require_privileges("sample:update") ],
    summary="Update a sample"
)
@log_activity(success_event_type="SAMPLE_UPDATE_VIA_API_SUCCESS", failure_event_type="SAMPLE_UPDATE_VIA_API_FAILURE")
async def update_sample( # Renamed from update_sample
    sample_id: UUID,
    sample_in: SampleUpdate,
    request: Request, # Added request
    db: Session = Depends(get_db),
):
    # SampleService.update_sample is now async and expects request
    return await SampleService(db).update_sample(sample_id, sample_in, request=request)

@router.delete(
    "/{sample_id}",
    response_model=SampleResponse,
    dependencies=[ require_privileges("sample:delete") ],
    summary="Delete a sample"
)
async def delete_sample( # Renamed from delete_sample
    sample_id: UUID,
    request: Request, # Added request, though not decorating this endpoint in PoC
    hard_delete: bool = Query(False, description="Permanently delete the sample"),
    db: Session = Depends(get_db),
):
    # SampleService.delete_sample is now async and expects request
    return await SampleService(db).delete_sample(sample_id, hard_delete, request=request)
