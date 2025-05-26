import logging
import json
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from sqlalchemy.orm import Session # Added for type hinting

from services.admin_logging_setting_service import AdminLoggingSettingService # Added

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(), # This will be our structured dict
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        # If record.msg is already a dict, use it as the base for the 'message' field content
        if isinstance(record.msg, dict):
            log_record["message"] = record.msg # Replace default message string with the dict
        return json.dumps(log_record)

class ActivityLoggerService:
    _instance = None
    _initialized_logger_config = False # For logger setup (handlers, formatter)
    _initialized_db_config = False # For DB dependent settings

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ActivityLoggerService, cls).__new__(cls)
        return cls._instance

    def __init__(self, db: Session = None, log_file_path: str = "logs/activity.log"):
        # Initialize logger (handlers, formatter) only once
        if not self._initialized_logger_config:
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            self.logger = logging.getLogger("activity_logger")
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False

            if not self.logger.handlers:
                handler = TimedRotatingFileHandler(
                    log_file_path, when='midnight', interval=1, backupCount=7, encoding='utf-8'
                )
                formatter = JsonFormatter()
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            self._initialized_logger_config = True

        # Initialize DB-dependent config only once, and only if db is provided
        if db and not self._initialized_db_config:
            self.admin_logging_setting_service = AdminLoggingSettingService(db)
            self.admin_logging_setting_service.initialize_default_settings()
            self.config = self.admin_logging_setting_service.get_all_settings()
            self._initialized_db_config = True
        elif not hasattr(self, 'config'): # Ensure config exists even if db not provided initially
             self.config = {}


    def reload_config(self, db: Session):
        """Reloads the logging configuration from the database. Requires a DB session."""
        if not hasattr(self, 'admin_logging_setting_service') or self.admin_logging_setting_service.repository.db != db :
            # Initialize service if it wasn't (e.g. initial call with db=None) or if db session changed
            self.admin_logging_setting_service = AdminLoggingSettingService(db)
            # Potentially re-initialize defaults if it's a new DB context, though initialize_default_settings is idempotent
            self.admin_logging_setting_service.initialize_default_settings()
        
        self.config = self.admin_logging_setting_service.get_all_settings()
        # print(f"ActivityLoggerService: Configuration reloaded. Current config: {self.config}")
        self._initialized_db_config = True # Mark DB config as initialized/updated


    def log(self, event_details: dict):
        """
        Logs the event details if the corresponding event_type is enabled in settings.
        The event_details dictionary is passed directly as the message.
        It must contain an 'event_type' key that corresponds to a setting_name
        in the admin_logging_settings table.
        """
        if not self._initialized_db_config:
            # This might happen if the service was initialized without a DB session
            # and reload_config hasn't been called with one.
            # Log to console as a fallback, or queue, or drop. For now, print a warning.
            # print(f"ActivityLoggerService: DB-dependent configuration not loaded. Event for '{event_details.get('event_type')}' cannot be checked against DB settings. Logging directly.")
            # self.logger.info(event_details) # Option: log anyway
            return # Option: drop if config not loaded

        event_type_to_log = event_details.get("event_type")
        if not event_type_to_log:
            # If event_type is missing, decide on a policy.
            # For now, we'll log it if a "REQUEST_RESPONSE_CYCLE" (the default from middleware) is enabled,
            # or if a generic "UNCLASSIFIED_EVENTS" setting were enabled.
            # Current middleware always adds "REQUEST_RESPONSE_CYCLE", so this path is less likely for those.
            # If truly no event_type, we default to not logging it.
            # print(f"ActivityLoggerService: Attempted to log event without 'event_type': {event_details.get('details', 'No details')}")
            return

        # Check against loaded configuration. Default to False (don't log) if not explicitly enabled.
        if self.config.get(event_type_to_log, False):
            self.logger.info(event_details)
        # else:
        #     print(f"ActivityLoggerService: Event type '{event_type_to_log}' is disabled. Not logging event: {event_details.get('details', 'No details')}")

# Example usage (optional, for direct testing of the service)
# Note: This example usage needs to be adapted as __init__ now requires a db Session
# for full functionality.
if __name__ == "__main__":
    # This part needs a proper DB session setup to run.
    # from core.database import SessionLocal
    # db_session = SessionLocal()
    # try:
    #     # Initializing with a DB session
    #     logger_service_with_db = ActivityLoggerService(db=db_session)
        
    #     print("Initial logging config:", logger_service_with_db.config)

    #     test_event_enabled = {
    #         "event_type": "AUTH_LOGIN_SUCCESS", # Assuming this is enabled by default
    #         "user_email": "test@example.com",
    #         "request_ip_address": "127.0.0.1",
    #         "details": "This is a test log event for an enabled type."
    #     }
    #     logger_service_with_db.log(test_event_enabled)
    #     print(f"Test log for AUTH_LOGIN_SUCCESS sent. Check {os.path.abspath('logs/activity.log')}")

    #     # Simulate a config change in DB and reload
    #     # This would typically be done via the API by an admin
    #     # For example, AdminLoggingSettingService(db_session).update_setting("AUTH_LOGIN_SUCCESS", False)
    #     # Then, logger_service_with_db.reload_config(db=db_session)
    #     # print("Simulated config update. Reloaded config:", logger_service_with_db.config)
        
    #     # Test again after "disabling"
    #     # logger_service_with_db.log(test_event_enabled) 
    #     # print(f"Test log for AUTH_LOGIN_SUCCESS attempted again. Check logs (should not appear if disabled).")

    # finally:
    #     db_session.close()
    pass
    #     "user_email": "test@example.com",
    #     "request_ip_address": "127.0.0.1",
    #     "details": "This is a test log event from direct execution."
    # }
    # logger_service.log(test_event)
    
    # # Verify by checking the logs/activity.log file
    # print(f"Test log sent. Check {os.path.abspath('logs/activity.log')}")
    
    # # Test with non-dict message to see basic formatting
    # # logger_service.logger.info("This is a simple string message, not a dict.")
    # # print(f"Test string log sent. Check {os.path.abspath('logs/activity.log')}")
