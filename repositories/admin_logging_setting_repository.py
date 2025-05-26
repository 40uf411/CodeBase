from typing import List, Dict, Any, Optional
from uuid import UUID # Added UUID for id type consistency
from sqlalchemy import select # Added
from sqlalchemy.ext.asyncio import AsyncSession # Added

from models.admin_logging_setting import AdminLoggingSetting
from repositories.base_repository import BaseRepository

class AdminLoggingSettingRepository(BaseRepository[AdminLoggingSetting]):
    def __init__(self, db: AsyncSession): # Updated to AsyncSession
        # AdminLoggingSetting does not have 'is_deleted' or 'soft_delete'
        # BaseRepository methods assume these. This needs careful handling.
        # For this refactor, we'll assume AdminLoggingSetting will behave like hard_delete always.
        super().__init__(AdminLoggingSetting, db)

    async def get_by_name(self, name: str) -> Optional[AdminLoggingSetting]:
        query = select(AdminLoggingSetting).filter(AdminLoggingSetting.setting_name == name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_settings(self) -> List[AdminLoggingSetting]:
        query = select(AdminLoggingSetting)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_setting(self, name: str, is_enabled: bool) -> Optional[AdminLoggingSetting]:
        setting = await self.get_by_name(name)
        if setting:
            setting.is_enabled = is_enabled
            self.db.add(setting) # Add to session before flush
            await self.db.flush()
            await self.db.refresh(setting)
            return setting
        return None

    async def create_or_update_bulk(self, settings_data: List[Dict[str, Any]]) -> List[AdminLoggingSetting]:
        """
        Creates new settings or updates existing ones based on setting_name.
        Expects a list of dictionaries, each with 'setting_name', 'is_enabled', and 'description'.
        """
        processed_settings = [] # Store all settings that are processed (created or updated)
        settings_to_refresh = [] # Store settings that actually changed or were created

        for setting_info in settings_data:
            existing_setting = await self.get_by_name(setting_info["setting_name"])
            if existing_setting:
                changed = False
                if "is_enabled" in setting_info and existing_setting.is_enabled != setting_info["is_enabled"]:
                    existing_setting.is_enabled = setting_info["is_enabled"]
                    changed = True
                if "description" in setting_info and existing_setting.description != setting_info["description"]:
                    existing_setting.description = setting_info["description"]
                    changed = True
                
                if changed:
                    self.db.add(existing_setting) # Add to session if changed
                    settings_to_refresh.append(existing_setting)
                processed_settings.append(existing_setting)
            else:
                new_setting = AdminLoggingSetting(
                    setting_name=setting_info["setting_name"],
                    is_enabled=setting_info.get("is_enabled", True),
                    description=setting_info.get("description")
                )
                self.db.add(new_setting)
                settings_to_refresh.append(new_setting) # New settings need to be added and refreshed
                processed_settings.append(new_setting)
        
        if settings_to_refresh: # Only flush and refresh if there are changes or new items
            await self.db.flush()
            for setting in settings_to_refresh:
                await self.db.refresh(setting)
            
        return processed_settings # Return all settings that were part of the input, with updates

    # Note: The BaseRepository's create, update, delete methods might need adjustment
    # or specific overrides if AdminLoggingSetting model doesn't fully align
    # with BaseRepository's assumptions (e.g., 'is_deleted' field).
    # For now, we assume they are okay, or will be handled if issues arise.
    # The `delete` method in BaseRepository now handles hard_delete correctly.
    # AdminLoggingSetting does not have `is_deleted` so soft delete is not applicable.
    # The `get` method in BaseRepository also checks for `is_deleted` if the attribute exists.
    # For AdminLoggingSetting, this check will be skipped by hasattr in Base.get if it's not there.

    async def get(self, id: UUID) -> Optional[AdminLoggingSetting]:
        # Override if BaseRepository.get's is_deleted check is problematic
        # For AdminLoggingSetting, 'is_deleted' is not present.
        # db.get directly fetches by PK, which is fine.
        return await self.db.get(self.model, id)

    async def create(self, data: Dict[str, Any]) -> AdminLoggingSetting:
        return await super().create(data)

    async def update(self, id: UUID, data: Dict[str, Any]) -> Optional[AdminLoggingSetting]:
        # Ensure id is UUID as expected by base
        return await super().update(id, data)

    async def delete(self, id: UUID, hard_delete: bool = True) -> Optional[AdminLoggingSetting]:
        # AdminLoggingSetting should always be hard-deleted as it has no soft-delete mechanism.
        # The base delete method will perform a hard delete if obj.is_deleted doesn't exist.
        # However, to be explicit, we force hard_delete = True.
        
        # The base 'get' method, if used by base 'delete', might look for 'is_deleted'.
        # We can call self.get (which is overridden here to not check is_deleted)
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        await self.db.delete(db_obj)
        await self.db.flush()
        return db_obj

# Dependency provider function
from fastapi import Depends
from core.database import get_async_db

def get_admin_logging_setting_repository(db: AsyncSession = Depends(get_async_db)) -> AdminLoggingSettingRepository:
    return AdminLoggingSettingRepository(db)
