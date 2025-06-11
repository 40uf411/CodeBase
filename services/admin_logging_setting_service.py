from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from repositories.admin_logging_setting_repository import AdminLoggingSettingRepository
from models.admin_logging_setting import AdminLoggingSetting # For type hinting if needed

class AdminLoggingSettingService:
    def __init__(self, db: Session):  # Changed to accept Session directly
        self.db = db
        self.repository = AdminLoggingSettingRepository(db)

    def get_all_settings(self) -> Dict[str, bool]:
        """
        Retrieves all logging settings and returns them as a dictionary
        of setting_name: is_enabled.
        """
        settings_list = self.repository.get_all_settings()
        return {setting.setting_name: setting.is_enabled for setting in settings_list}

    def update_setting(self, name: str, is_enabled: bool) -> Optional[Dict[str, bool]]:
        """
        Updates a single logging setting.
        Returns a dictionary of the updated setting or None if not found.
        """
        # Repository method update_setting no longer commits. Service must commit.
        # It also returns Optional[AdminLoggingSetting] from the repo.
        try:
            updated_setting_obj = self.repository.update_setting(name, is_enabled) # This gets from repo, which returns Optional[model]
            if not updated_setting_obj:
                # This means the setting was not found by the repository's get_by_name
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Logging setting '{name}' not found.")
            
            # updated_setting_obj now holds the model instance with is_enabled potentially changed by repo.update_setting
            # The repo.update_setting method itself does not commit.
            self.db.commit()
            self.db.refresh(updated_setting_obj) # Ensure state is fresh from DB after commit
            return updated_setting_obj # Return the ORM object
        except HTTPException: # Re-raise HTTPException specifically if we want to keep its status/detail
            raise
        except Exception as e: # Catch other potential errors during commit etc.
            self.db.rollback()
            # Optionally log the exception e
            # Consider raising a service-specific exception or re-raising a generic 500
            # For now, re-raising the original error to be handled by FastAPI error handlers or middleware
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while updating setting '{name}'.")

    def initialize_default_settings(self):
        """
        Initializes the database with a predefined list of default logging settings
        if they don't already exist or if some are missing.
        This is idempotent.
        """
        default_settings_data = [
            {"setting_name": "AUTH_LOGIN_SUCCESS", "is_enabled": True, "description": "Log successful user logins."},
            {"setting_name": "AUTH_LOGIN_FAILURE", "is_enabled": True, "description": "Log failed user login attempts."},
            {"setting_name": "AUTH_LOGOUT_SUCCESS", "is_enabled": True, "description": "Log successful user logouts."},
            {"setting_name": "AUTH_TOKEN_REFRESHED", "is_enabled": True, "description": "Log successful token refreshes."},
            {"setting_name": "AUTH_PASSWORD_RESET_REQUEST", "is_enabled": True, "description": "Log password reset requests."},
            {"setting_name": "AUTH_PASSWORD_RESET_SUCCESS", "is_enabled": True, "description": "Log successful password resets."},
            {"setting_name": "AUTH_REGISTRATION_SUCCESS", "is_enabled": True, "description": "Log new user registrations."},
            
            {"setting_name": "RESOURCE_CREATE", "is_enabled": True, "description": "Log creation of resources (e.g., users, roles, samples)."},
            {"setting_name": "RESOURCE_READ_ONE", "is_enabled": True, "description": "Log retrieval of a single resource."},
            {"setting_name": "RESOURCE_READ_LIST", "is_enabled": True, "description": "Log retrieval of a list of resources."},
            {"setting_name": "RESOURCE_UPDATE", "is_enabled": True, "description": "Log updates to resources."},
            {"setting_name": "RESOURCE_DELETE", "is_enabled": True, "description": "Log deletion of resources."},
            
            {"setting_name": "PRIVILEGE_ASSIGNED", "is_enabled": True, "description": "Log assignment of privileges to roles."},
            {"setting_name": "PRIVILEGE_REMOVED", "is_enabled": True, "description": "Log removal of privileges from roles."},
            {"setting_name": "ROLE_ASSIGNED_TO_USER", "is_enabled": True, "description": "Log assignment of roles to users."}, # Assuming this might be needed
            {"setting_name": "ROLE_REMOVED_FROM_USER", "is_enabled": True, "description": "Log removal of roles from users."}, # Assuming this might be needed

            {"setting_name": "SYSTEM_ERROR", "is_enabled": True, "description": "Log unexpected system errors or exceptions."},
            {"setting_name": "SECURITY_ALERT", "is_enabled": True, "description": "Log potential security-related events (e.g., unauthorized access attempts)."},
            
            {"setting_name": "LOG_DATA_MODIFICATIONS", "is_enabled": False, "description": "Log modifications to log data settings themselves. (Default: False to prevent log flooding)."},
            {"setting_name": "REQUEST_RESPONSE_CYCLE", "is_enabled": True, "description": "General logging for each request-response cycle by ActivityLoggingMiddleware."}
        ]
        
        # This uses the repository's method that handles both creation of new settings
        # and updates to existing ones (e.g., if a description changed).
        # Repository method create_or_update_bulk no longer commits. Service must commit.
        # For settings not in default_settings_data but in DB, they will be untouched.
        try:
            # The repository method stages all changes (adds new, updates existing in session)
            updated_or_created_settings = self.repository.create_or_update_bulk(default_settings_data)
            self.db.commit()
            # Refresh objects if needed (repo method already does this for new/dirty items before returning)
            # for setting in updated_or_created_settings:
            #     if setting in self.db: # Ensure they are persistent or part of session
            #         self.db.refresh(setting)
            # print(f"Default logging settings initialized/verified. {len(default_settings_data)} settings processed.")
        except Exception as e:
            self.db.rollback()
            # Optionally log the exception e
            # print(f"Error initializing default settings: {e}")
            raise # Re-raise for now, or handle more gracefully

# Example of how this service might be instantiated and used (for testing or in main.py)
if __name__ == "__main__":
    # This requires a database session. For standalone testing, you'd set up an in-memory SQLite DB or connect to dev DB.
    # from core.database import SessionLocal # Assuming you have this
    # db_session = SessionLocal()
    # try:
    #     service = AdminLoggingSettingService(db_session)
    #     service.initialize_default_settings()
    #     all_settings = service.get_all_settings()
    #     print("Current logging settings:", all_settings)
        
    #     # Example update
    #     if "AUTH_LOGIN_SUCCESS" in all_settings:
    #         updated = service.update_setting("AUTH_LOGIN_SUCCESS", False)
    #         print("Updated AUTH_LOGIN_SUCCESS:", updated)
    #         all_settings_after_update = service.get_all_settings()
    #         print("All settings after update:", all_settings_after_update)
    # finally:
    #     db_session.close()
    pass
