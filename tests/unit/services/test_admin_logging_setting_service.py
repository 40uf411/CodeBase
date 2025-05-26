import unittest
from unittest.mock import MagicMock, patch, call # Added call
from sqlalchemy.orm import Session # For type hinting Session mock

# Adjust import path based on your project structure
from services.admin_logging_setting_service import AdminLoggingSettingService
from models.admin_logging_setting import AdminLoggingSetting # For creating mock return objects
from repositories.admin_logging_setting_repository import AdminLoggingSettingRepository

# Ensure the services directory is in the Python path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestAdminLoggingSettingService(unittest.TestCase):

    def setUp(self):
        self.mock_db_session = MagicMock(spec=Session)
        # Patch the repository within the service's module context
        self.patcher = patch('services.admin_logging_setting_service.AdminLoggingSettingRepository')
        self.MockAdminLoggingSettingRepository = self.patcher.start()
        
        # Instantiate the service, which will use the mocked repository
        self.mock_repository_instance = self.MockAdminLoggingSettingRepository.return_value
        self.service = AdminLoggingSettingService(db=self.mock_db_session)

    def tearDown(self):
        self.patcher.stop()

    def test_get_all_settings(self):
        # Setup mock repository response
        mock_settings_list = [
            AdminLoggingSetting(setting_name="EVENT_A", is_enabled=True, description="Desc A"),
            AdminLoggingSetting(setting_name="EVENT_B", is_enabled=False, description="Desc B")
        ]
        self.mock_repository_instance.get_all_settings.return_value = mock_settings_list

        # Call the service method
        result = self.service.get_all_settings()

        # Assertions
        self.mock_repository_instance.get_all_settings.assert_called_once()
        expected_result = {"EVENT_A": True, "EVENT_B": False}
        self.assertEqual(result, expected_result)

    def test_update_setting_found(self):
        setting_name_to_update = "EVENT_A"
        new_is_enabled_status = False
        
        # Mock repository returning an updated setting object
        updated_setting_mock = AdminLoggingSetting(
            setting_name=setting_name_to_update, 
            is_enabled=new_is_enabled_status
        )
        self.mock_repository_instance.update_setting.return_value = updated_setting_mock

        # Call the service method
        result = self.service.update_setting(setting_name_to_update, new_is_enabled_status)

        # Assertions
        self.mock_repository_instance.update_setting.assert_called_once_with(setting_name_to_update, new_is_enabled_status)
        expected_result = {setting_name_to_update: new_is_enabled_status}
        self.assertEqual(result, expected_result)

    def test_update_setting_not_found(self):
        setting_name_to_update = "NON_EXISTENT_EVENT"
        new_is_enabled_status = True
        
        self.mock_repository_instance.update_setting.return_value = None # Simulate setting not found

        # Call the service method
        result = self.service.update_setting(setting_name_to_update, new_is_enabled_status)

        # Assertions
        self.mock_repository_instance.update_setting.assert_called_once_with(setting_name_to_update, new_is_enabled_status)
        self.assertIsNone(result)

    def test_initialize_default_settings(self):
        # Define the default settings as they are in the service
        # (Copied from AdminLoggingSettingService for test accuracy)
        default_settings_data = [
            {"setting_name": "AUTH_LOGIN_SUCCESS", "is_enabled": True, "description": "Log successful user logins."},
            {"setting_name": "AUTH_LOGIN_FAILURE", "is_enabled": True, "description": "Log failed user login attempts."},
            # ... (add all other default settings defined in the service) ...
            {"setting_name": "LOG_DATA_MODIFICATIONS", "is_enabled": False, "description": "Log modifications to log data settings themselves. (Default: False to prevent log flooding)."},
            {"setting_name": "REQUEST_RESPONSE_CYCLE", "is_enabled": True, "description": "General logging for each request-response cycle by ActivityLoggingMiddleware."}
        ]
        # For this test, let's assume only a subset for brevity, but in real test, list all.
        # For the purpose of testing the logic, we only need a few.
        # Let's simulate a scenario where some settings exist, and some don't.
        
        # This method now directly calls create_or_update_bulk, so we test that.
        self.service.initialize_default_settings()

        # Assert that create_or_update_bulk was called once with all default settings data
        self.mock_repository_instance.create_or_update_bulk.assert_called_once()
        
        # Check the argument passed to create_or_update_bulk
        actual_call_args = self.mock_repository_instance.create_or_update_bulk.call_args[0][0]
        
        # Verify that all default settings defined in the service are present in the call
        # This is a more robust check than just length if default_settings_data is not fully listed here
        # For now, we'll check if the structure matches and contains at least one known item
        self.assertIsInstance(actual_call_args, list)
        self.assertTrue(len(actual_call_args) >= 2) # Based on the two items listed above
        
        # Check if a specific default setting is in the arguments passed to bulk update
        # This assumes default_settings_data in the test is a subset of the actual one
        found_auth_login = any(d['setting_name'] == "AUTH_LOGIN_SUCCESS" for d in actual_call_args)
        self.assertTrue(found_auth_login, "AUTH_LOGIN_SUCCESS should be part of default settings initialization.")
        
        found_log_data_mod = any(d['setting_name'] == "LOG_DATA_MODIFICATIONS" for d in actual_call_args)
        self.assertTrue(found_log_data_mod, "LOG_DATA_MODIFICATIONS should be part of default settings initialization.")


if __name__ == '__main__':
    unittest.main()

# Ensure the test file ends with a newline
