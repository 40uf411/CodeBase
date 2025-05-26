from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import require_privileges # Assuming this utility for privilege checking
from services.admin_logging_setting_service import AdminLoggingSettingService
from schemas.admin_logging_setting_schema import LoggingSettingUpdate, LoggingSettingResponse

router = APIRouter(
    prefix="/admin/logging-settings",
    tags=["Admin Logging Settings"],
    # This is a placeholder for actual privilege checking.
    # The privilege "admin:logging_settings:manage" should be created and assigned.
    dependencies=[Depends(require_privileges("admin:logging_settings:manage"))] 
)

def get_admin_logging_setting_service(db: Session = Depends(get_db)) -> AdminLoggingSettingService:
    return AdminLoggingSettingService(db)

@router.get(
    "/",
    response_model=List[LoggingSettingResponse],
    summary="List all logging settings",
    description="Retrieves all configurable logging settings and their current status."
)
async def list_logging_settings(
    service: AdminLoggingSettingService = Depends(get_admin_logging_setting_service)
):
    # The service's get_all_settings returns Dict[str, bool]
    # We need to convert this to List[LoggingSettingResponse]
    # For that, we need the full setting objects from the repository layer
    # Let's adjust the service or add a method to the repository/service to get full objects
    
    # Quick adjustment: Fetch full objects via repository for now for the response model
    settings_objects = service.repository.get_all_settings()
    return settings_objects


@router.put(
    "/{setting_name}",
    response_model=LoggingSettingResponse,
    summary="Update a specific logging setting",
    description="Enable or disable a specific logging setting by its name."
)
async def update_logging_setting(
    setting_name: str,
    setting_update: LoggingSettingUpdate,
    service: AdminLoggingSettingService = Depends(get_admin_logging_setting_service)
):
    # The service's update_setting method now:
    # 1. Calls the repository's update_setting (which finds by name).
    # 2. If not found by repo, the service raises HTTPException(404).
    # 3. Commits and refreshes the ORM object.
    # 4. Returns the updated ORM object.
    # Thus, the router can directly call it and return the result.
    # Any exceptions (404 from service, 500 from service) will be propagated.
    
    updated_setting_orm_obj = service.update_setting(setting_name, setting_update.is_enabled)
    # If service.update_setting completes without raising an exception,
    # updated_setting_orm_obj is the AdminLoggingSetting ORM model instance.
    # This matches the response_model=LoggingSettingResponse which expects an ORM object
    # or a dict that can be parsed into it (Pydantic's orm_mode=True).
    return updated_setting_orm_obj
