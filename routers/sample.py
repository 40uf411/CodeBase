from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, status, Request # Added Request
from sqlalchemy.orm import Session

# from core.database import get_db # Replaced by service dependency
from utils.activity_logging_decorators import log_activity # Added
from core.auth import require_privileges
from services.sample_service import SampleService, get_sample_service # Added get_sample_service
# from services.privilege_service import PrivilegeService # No longer directly used in create_sample
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
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    # sample_service = SampleService(db) # Removed
    # SampleService.create_sample is now async and expects request
    # It also handles privilege creation internally.
    sample = await sample_service.create_sample(sample_in, request=request) # Changed
    # ensure CRUD privileges exist
    # PrivilegeService(db).create_crud_privileges("sample") # This is handled by SampleService.create_sample
    return sample

@router.get(
    "/",
    response_model=List[SampleResponse],
    summary="List samples"
)
async def list_samples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    return sample_service.get_samples(skip=skip, limit=limit) # Changed

@router.get(
    "/active",
    response_model=List[SampleResponse],
    summary="List active samples"
)
async def list_active_samples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    return sample_service.get_active_samples(skip=skip, limit=limit) # Changed

@router.get(
    "/priority/{priority}",
    response_model=List[SampleResponse],
    summary="List samples by priority"
)
async def list_samples_by_priority(
    priority: int = Path(..., title="Priority", ge=1, le=5), # Added title for clarity
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    return sample_service.get_by_priority(priority, skip=skip, limit=limit) # Changed

@router.get(
    "/{sample_id}",
    response_model=SampleResponse,
    summary="Get a sample"
)
async def get_sample( 
    sample_id: UUID,
    request: Request, # Added request, though not decorating this endpoint in PoC
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    # SampleService.get_sample is now async and expects request
    return await sample_service.get_sample(sample_id, request=request) # Changed

@router.put(
    "/{sample_id}",
    response_model=SampleResponse,
    dependencies=[ require_privileges("sample:update") ],
    summary="Update a sample"
)
@log_activity(success_event_type="SAMPLE_UPDATE_VIA_API_SUCCESS", failure_event_type="SAMPLE_UPDATE_VIA_API_FAILURE")
async def update_sample( 
    sample_id: UUID,
    sample_in: SampleUpdate,
    request: Request, # Added request
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    # SampleService.update_sample is now async and expects request
    return await sample_service.update_sample(sample_id, sample_in, request=request) # Changed

@router.delete(
    "/{sample_id}",
    response_model=SampleResponse,
    dependencies=[ require_privileges("sample:delete") ],
    summary="Delete a sample"
)
async def delete_sample( 
    sample_id: UUID,
    request: Request, # Added request, though not decorating this endpoint in PoC
    hard_delete: bool = Query(False, description="Permanently delete the sample"),
    sample_service: SampleService = Depends(get_sample_service), # Changed
):
    # SampleService.delete_sample is now async and expects request
    return await sample_service.delete_sample(sample_id, hard_delete, request=request) # Changed
