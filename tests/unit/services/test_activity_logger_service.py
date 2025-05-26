import unittest
from unittest.mock import patch, MagicMock, call
import logging
import os

# Adjust import path based on your project structure
# Assuming 'services' is a top-level directory or discoverable in PYTHONPATH
from services.activity_logger_service import ActivityLoggerService, JsonFormatter
from sqlalchemy.orm import Session # For type hinting if needed for Session mock

# Ensure the services directory is in the Python path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestJsonFormatter(unittest.TestCase):
    def test_format_dict_message(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test_pathname',
            lineno=123,
            msg={'custom_key': 'custom_value', 'event_type': 'TEST_EVENT'},
            args=(),
            exc_info=None,
            func='test_func'
        )
        # Simulate that record.created is set by logging.makeLogRecord
        record.created = 1678886400.0 # Example: 2023-03-15 12:00:00 UTC

        formatted_json_str = formatter.format(record)
        formatted_dict = json.loads(formatted_json_str)

        self.assertEqual(formatted_dict['level'], 'INFO')
        self.assertEqual(formatted_dict['module'], 'test_pathname') # module comes from pathname
        self.assertEqual(formatted_dict['funcName'], 'test_func')
        self.assertEqual(formatted_dict['lineno'], 123)
        # Timestamp format: "YYYY-MM-DDTHH:MM:SS.ffffffZ" or similar if timezone.utc
        self.assertIn("2023-03-15T12:00:00", formatted_dict['timestamp']) 
        
        # Check that the original dict message is now the 'message' field
        self.assertEqual(formatted_dict['message']['custom_key'], 'custom_value')
        self.assertEqual(formatted_dict['message']['event_type'], 'TEST_EVENT')

    def test_format_string_message(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name='test_logger',
            level=logging.WARNING,
            pathname='another_test',
            lineno=10,
            msg="This is a string message",
            args=(),
            exc_info=None,
            func='another_func'
        )
        record.created = 1678886400.0

        formatted_json_str = formatter.format(record)
        formatted_dict = json.loads(formatted_json_str)

        self.assertEqual(formatted_dict['level'], 'WARNING')
        self.assertEqual(formatted_dict['message'], "This is a string message")


# Patch logging.getLogger and TimedRotatingFileHandler for all tests in TestActivityLoggerService
@patch('services.activity_logger_service.logging.getLogger')
@patch('services.activity_logger_service.TimedRotatingFileHandler')
@patch('services.activity_logger_service.os.makedirs') # Mock makedirs
@patch('services.activity_logger_service.AdminLoggingSettingService') # Mock the admin service dependency
class TestActivityLoggerService(unittest.TestCase):

    def setUp(self):
        # Reset singleton instance for each test to ensure clean state
        ActivityLoggerService._instance = None
        ActivityLoggerService._initialized_logger_config = False
        ActivityLoggerService._initialized_db_config = False
        
        # Mock the DB session
        self.mock_db_session = MagicMock(spec=Session)


    def test_singleton_behavior(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        MockAdminService.return_value.get_all_settings.return_value = {} # Default empty config

        instance1 = ActivityLoggerService(db=self.mock_db_session, log_file_path="test_logs/activity.log")
        instance2 = ActivityLoggerService(db=self.mock_db_session, log_file_path="test_logs/activity.log")
        
        self.assertIs(instance1, instance2)
        # Ensure logger and handler setup only called once by the first instance
        MockGetLogger.assert_called_once_with("activity_logger")
        MockTimedRotatingFileHandler.assert_called_once()
        mock_logger.addHandler.assert_called_once()
        MockAdminService.assert_called_once_with(self.mock_db_session)
        MockAdminService.return_value.initialize_default_settings.assert_called_once()
        MockAdminService.return_value.get_all_settings.assert_called_once()


    def test_logger_initialization(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        MockAdminService.return_value.get_all_settings.return_value = {}

        log_file_path = "custom_path/activity.log"
        ActivityLoggerService(db=self.mock_db_session, log_file_path=log_file_path)

        MockMakeDirs.assert_called_once_with(os.path.dirname(log_file_path), exist_ok=True)
        MockGetLogger.assert_called_once_with("activity_logger")
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        self.assertFalse(mock_logger.propagate)

        MockTimedRotatingFileHandler.assert_called_once_with(
            log_file_path,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        
        mock_handler_instance = MockTimedRotatingFileHandler.return_value
        mock_handler_instance.setFormatter.assert_called_once()
        formatter_arg = mock_handler_instance.setFormatter.call_args[0][0]
        self.assertIsInstance(formatter_arg, JsonFormatter)
        
        mock_logger.addHandler.assert_called_once_with(mock_handler_instance)
        
        # Test AdminLoggingSettingService initialization
        MockAdminService.assert_called_once_with(self.mock_db_session)
        mock_admin_service_instance = MockAdminService.return_value
        mock_admin_service_instance.initialize_default_settings.assert_called_once()
        mock_admin_service_instance.get_all_settings.assert_called_once()


    def test_log_event_enabled(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        # Simulate that the 'TEST_EVENT' is enabled in config
        mock_config = {"TEST_EVENT": True, "OTHER_EVENT": False}
        MockAdminService.return_value.get_all_settings.return_value = mock_config

        service = ActivityLoggerService(db=self.mock_db_session)
        service.config = mock_config # Ensure config is set for this test instance

        event_details = {"event_type": "TEST_EVENT", "data": "some_data"}
        service.log(event_details)
        
        mock_logger.info.assert_called_once_with(event_details)

    def test_log_event_disabled(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        mock_config = {"TEST_EVENT": True, "OTHER_EVENT": False}
        MockAdminService.return_value.get_all_settings.return_value = mock_config

        service = ActivityLoggerService(db=self.mock_db_session)
        service.config = mock_config

        event_details_disabled = {"event_type": "OTHER_EVENT", "data": "other_data"}
        service.log(event_details_disabled)
        
        mock_logger.info.assert_not_called()

    def test_log_event_type_missing_in_config(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        mock_config = {"EXISTING_EVENT": True} # Does not contain 'NEW_EVENT'
        MockAdminService.return_value.get_all_settings.return_value = mock_config
        
        service = ActivityLoggerService(db=self.mock_db_session)
        service.config = mock_config

        event_details_new = {"event_type": "NEW_EVENT", "data": "new_data"}
        service.log(event_details_new) # Should default to False
        
        mock_logger.info.assert_not_called()

    def test_log_event_type_not_in_event_details(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        mock_logger = MockGetLogger.return_value
        MockAdminService.return_value.get_all_settings.return_value = {"ANY_EVENT": True}
        
        service = ActivityLoggerService(db=self.mock_db_session)
        
        event_details_no_type = {"data": "some_data_no_type"} # Missing 'event_type'
        service.log(event_details_no_type)
        
        mock_logger.info.assert_not_called() # Current logic: if no event_type, don't log

    def test_reload_config(self, MockAdminService, MockMakeDirs, MockTimedRotatingFileHandler, MockGetLogger):
        MockAdminService.return_value.get_all_settings.side_effect = [
            {"EVENT_A": True}, # Initial config
            {"EVENT_A": False, "EVENT_B": True}  # New config after reload
        ]
        
        service = ActivityLoggerService(db=self.mock_db_session)
        self.assertTrue(service.config.get("EVENT_A"))
        self.assertNotIn("EVENT_B", service.config)

        # Create a new mock session for reload to simulate different context if needed
        new_mock_db_session = MagicMock(spec=Session)
        service.reload_config(db=new_mock_db_session)
        
        # Check AdminLoggingSettingService was re-initialized or re-used with new session for get_all_settings
        # The mock_admin_service_instance from setUp is based on self.mock_db_session
        # We need to check the calls on the new instance if it's re-created, or on the same mock if it's updated.
        # Current implementation of reload_config will create a new AdminLoggingSettingService instance
        # if the db session is different.
        self.assertEqual(MockAdminService.call_count, 2) # Once in __init__, once in reload_config
        MockAdminService.return_value.get_all_settings.assert_called_with() # Called twice
        
        self.assertFalse(service.config.get("EVENT_A"))
        self.assertTrue(service.config.get("EVENT_B"))


if __name__ == '__main__':
    # Need to load json for the JsonFormatter tests if run directly
    import json
    unittest.main()

# Ensure the test file ends with a newline
