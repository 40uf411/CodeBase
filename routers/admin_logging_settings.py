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
    # The service's update_setting expects name and is_enabled
    # It returns Dict[str, bool] or None.
    # We need to fetch the full object for LoggingSettingResponse
    
    original_setting = service.repository.get_by_name(setting_name)
    if not original_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Logging setting '{setting_name}' not found.")

    updated_setting_dict = service.update_setting(setting_name, setting_update.is_enabled)
    
    if updated_setting_dict is None: # Should not happen if original_setting was found, but as a safeguard
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update logging setting.")

    # Fetch the updated object to return in the defined response model
    # The service update_setting returns only a dict, so we refetch or adjust service.
    # For now, refetch:
    updated_db_setting = service.repository.get_by_name(setting_name)
    if not updated_db_setting:
         # This case should ideally not be reached if update was successful
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve setting post-update.")
        
    return updated_db_setting
