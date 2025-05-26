from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.admin_logging_setting import AdminLoggingSetting
from repositories.base_repository import BaseRepository # Assuming this exists

class AdminLoggingSettingRepository(BaseRepository[AdminLoggingSetting]):
    def __init__(self, db: Session):
        super().__init__(AdminLoggingSetting, db)

    def get_by_name(self, name: str) -> Optional[AdminLoggingSetting]:
        return self.db.query(AdminLoggingSetting).filter(AdminLoggingSetting.setting_name == name).first()

    def get_all_settings(self) -> List[AdminLoggingSetting]:
        return self.db.query(AdminLoggingSetting).all()

    def update_setting(self, name: str, is_enabled: bool) -> Optional[AdminLoggingSetting]:
        setting = self.get_by_name(name)
        if setting:
            setting.is_enabled = is_enabled
            # try: # Removed try/except for commit/rollback
            #     self.db.commit()
            self.db.refresh(setting) # Keep refresh
            return setting
            # except SQLAlchemyError as e:
            #     self.db.rollback()
            #     # Optionally log the error e
            #     raise e
        return None

    def create_or_update_bulk(self, settings_data: List[Dict[str, Any]]) -> List[AdminLoggingSetting]:
        """
        Creates new settings or updates existing ones based on setting_name.
        Expects a list of dictionaries, each with 'setting_name', 'is_enabled', and 'description'.
        """
        updated_settings = []
        created_settings_count = 0
        updated_settings_count = 0

        for setting_info in settings_data:
            existing_setting = self.get_by_name(setting_info["setting_name"])
            if existing_setting:
                # Update existing setting
                changed = False
                if "is_enabled" in setting_info and existing_setting.is_enabled != setting_info["is_enabled"]:
                    existing_setting.is_enabled = setting_info["is_enabled"]
                    changed = True
                if "description" in setting_info and existing_setting.description != setting_info["description"]:
                    existing_setting.description = setting_info["description"]
                    changed = True
                
                if changed:
                    updated_settings_count +=1
                updated_settings.append(existing_setting)
            else:
                # Create new setting
                new_setting = AdminLoggingSetting(
                    setting_name=setting_info["setting_name"],
                    is_enabled=setting_info.get("is_enabled", True), # Default to True if not provided
                    description=setting_info.get("description")
                )
                self.db.add(new_setting)
                updated_settings.append(new_setting)
                created_settings_count += 1
        
        # try: # Removed try/except for commit/rollback
        if created_settings_count > 0 or updated_settings_count > 0:
            # self.db.commit() # Removed commit
            for setting in updated_settings:
                if setting in self.db.dirty or setting in self.db.new: # Only refresh if part of current transaction changes
                     self.db.refresh(setting) # Refresh to get DB defaults like created_at, updated_at
        # For settings that were neither created nor updated but just fetched and added to updated_settings list
        # they don't need refreshing if they weren't modified.
        
        # print(f"Bulk operation: {created_settings_count} created, {updated_settings_count} updated.")
        # except SQLAlchemyError as e:
        #     self.db.rollback()
        #     # Optionally log the error e
        #     # print(f"Error in bulk create/update: {e}")
        #     raise e
            
        return updated_settings

    def create(self, data: Dict[str, Any]) -> AdminLoggingSetting:
        """
        Standard create method from BaseRepository, overridden for clarity if needed,
        or rely on BaseRepository's implementation.
        """
        return super().create(data)

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[AdminLoggingSetting]:
        """
        Standard update method from BaseRepository, overridden for clarity if needed,
        or rely on BaseRepository's implementation.
        """
        return super().update(id, data)

    def delete(self, id: Any, hard_delete: bool = False) -> Optional[AdminLoggingSetting]:
        """
        Standard delete method from BaseRepository, overridden for clarity if needed,
        or rely on BaseRepository's implementation.
        """
        # AdminLoggingSetting does not have is_deleted, so hard_delete is effectively always True
        # if it were to be used. Standard BaseRepository might need adjustment or this model
        # might not support soft delete. For now, assume direct delete.
        setting = self.get(id)
        if setting:
            self.db.delete(setting)
            # try: # Removed try/except for commit/rollback
            #     self.db.commit()
            return setting # No refresh needed as it's deleted
            # except SQLAlchemyError as e:
            #     self.db.rollback()
            #     raise e
        return None
