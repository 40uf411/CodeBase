import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import functools # For wraps, though not strictly needed for test structure
from fastapi import Request, HTTPException
from pydantic import BaseModel, Field

# Adjust import path based on your project structure
from utils.activity_logging_decorators import log_activity, SENSITIVE_FIELD_NAMES
from services.activity_logger_service import ActivityLoggerService # For type hint

# Ensure the utils directory is in the Python path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# --- Test Pydantic Models ---
class MockUserInputSchema(BaseModel):
    username: str
    password: str # Sensitive
    email: str
    
class MockUpdateSchema(BaseModel):
    description: str
    secret_field: str = Field(default="default_secret") # Sensitive

class MockResourceResponse(BaseModel):
    id: str
    name: str
    value: int


class TestLogActivityDecorator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_logger_service = MagicMock(spec=ActivityLoggerService)
        self.mock_logger_service.log = MagicMock() # Mock the log method itself
        
        # Mock request object and its state
        self.mock_request = MagicMock(spec=Request)
        self.mock_request.app = MagicMock()
        self.mock_request.app.state = MagicMock()
        self.mock_request.app.state.activity_logger_service = self.mock_logger_service

        # Default config for logger_service
        self.mock_logger_service.config = {
            "LOG_DATA_MODIFICATIONS": False, # Default to False
            # Add other event types if needed for specific tests
            "MOCK_CREATE_SUCCESS": True,
            "MOCK_UPDATE_SUCCESS": True,
            "MOCK_DELETE_SUCCESS": True,
            "MOCK_OPERATION_SUCCESS": True,
            "MOCK_OPERATION_FAILURE": True,
            "MOCK_HTTP_FAILURE": True,
            "MOCK_GENERAL_FAILURE": True,
        }

    # --- Test Decorated Functions ---
    async def test_success_path_basic_logging(self):
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS", failure_event_type="MOCK_OPERATION_FAILURE")
        async def mock_successful_operation(param1: str, request: Request, current_user: MagicMock = None):
            return {"status": "ok", "result_id": "res123"}

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.id = "user_uuid_123"

        await mock_successful_operation("value1", request=self.mock_request, current_user=mock_user)

        self.mock_logger_service.log.assert_called_once()
        logged_event = self.mock_logger_service.log.call_args[0][0]
        
        self.assertEqual(logged_event["event_type"], "MOCK_OPERATION_SUCCESS")
        self.assertEqual(logged_event["actor_user_email"], "test@example.com")
        self.assertEqual(logged_event["function_name"], "mock_successful_operation")
        self.assertIn("input_args_summary", logged_event)
        self.assertEqual(logged_event["input_args_summary"]["param1"], "value1")
        self.assertNotIn("data_changed_summary", logged_event) # LOG_DATA_MODIFICATIONS is False by default

    async def test_success_path_with_log_data_modifications_create(self):
        self.mock_logger_service.config["LOG_DATA_MODIFICATIONS"] = True
        
        @log_activity(success_event_type="MOCK_CREATE_SUCCESS", failure_event_type="MOCK_OPERATION_FAILURE")
        async def mock_create_operation(item_data: MockUserInputSchema, request: Request, current_user: MagicMock = None):
            return MockResourceResponse(id="new_item_id_789", name=item_data.username, value=100)

        mock_user = MagicMock(email="creator@example.com", id="creator_id")
        input_data = MockUserInputSchema(username="testuser", password="securepassword", email="newuser@example.com")

        await mock_create_operation(item_data=input_data, request=self.mock_request, current_user=mock_user)
        
        self.mock_logger_service.log.assert_called_once()
        logged_event = self.mock_logger_service.log.call_args[0][0]

        self.assertEqual(logged_event["event_type"], "MOCK_CREATE_SUCCESS")
        self.assertIn("data_changed_summary", logged_event)
        summary = logged_event["data_changed_summary"]
        
        self.assertIn("input_data", summary)
        self.assertEqual(summary["input_data"]["username"], "testuser")
        self.assertEqual(summary["input_data"]["email"], "newuser@example.com")
        self.assertNotIn("password", summary["input_data"]) # Sensitive field check

        self.assertEqual(summary["created_resource_id"], "new_item_id_789")
        self.assertIn("result_id:new_item_id_789", logged_event["target_resource_ids"])


    async def test_success_path_with_log_data_modifications_update(self):
        self.mock_logger_service.config["LOG_DATA_MODIFICATIONS"] = True

        @log_activity(success_event_type="MOCK_UPDATE_SUCCESS", failure_event_type="MOCK_OPERATION_FAILURE")
        async def mock_update_operation(item_id: str, update_data: MockUpdateSchema, request: Request, current_user: MagicMock = None):
            # Simulate returning the updated object or just a success status
            return {"id": item_id, "description": update_data.description, "status": "updated"}

        mock_user = MagicMock(email="updater@example.com", id="updater_id")
        update_payload = MockUpdateSchema(description="New Description", secret_field="new_secret")
        item_to_update_id = "item_xyz_123"

        await mock_update_operation(item_id=item_to_update_id, update_data=update_payload, request=self.mock_request, current_user=mock_user)
        
        self.mock_logger_service.log.assert_called_once()
        logged_event = self.mock_logger_service.log.call_args[0][0]
        
        self.assertEqual(logged_event["event_type"], "MOCK_UPDATE_SUCCESS")
        self.assertIn("data_changed_summary", logged_event)
        summary = logged_event["data_changed_summary"]

        self.assertIn(item_to_update_id, summary["target_resource_ids"])
        self.assertIn("update_payload", summary)
        self.assertEqual(summary["update_payload"]["description"], "New Description")
        self.assertNotIn("secret_field", summary["update_payload"]) # Sensitive field check
        self.assertIn(item_to_update_id, logged_event["target_resource_ids"]) # From kwargs extraction


    async def test_failure_path_http_exception(self):
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS", failure_event_type="MOCK_HTTP_FAILURE")
        async def mock_operation_http_fail(request: Request):
            raise HTTPException(status_code=403, detail="Permission Denied")

        with self.assertRaises(HTTPException):
            await mock_operation_http_fail(request=self.mock_request)

        self.mock_logger_service.log.assert_called_once()
        logged_event = self.mock_logger_service.log.call_args[0][0]

        self.assertEqual(logged_event["event_type"], "MOCK_HTTP_FAILURE")
        self.assertEqual(logged_event["error_message"], "Permission Denied")
        self.assertEqual(logged_event["status_code"], 403)
        self.assertNotIn("error_stacktrace", logged_event) # Stacktrace not typically for HTTPException by default

    async def test_failure_path_general_exception(self):
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS", failure_event_type="MOCK_GENERAL_FAILURE")
        async def mock_operation_general_fail(request: Request):
            raise ValueError("Something went very wrong")

        with self.assertRaises(ValueError):
            await mock_operation_general_fail(request=self.mock_request)

        self.mock_logger_service.log.assert_called_once()
        logged_event = self.mock_logger_service.log.call_args[0][0]

        self.assertEqual(logged_event["event_type"], "MOCK_GENERAL_FAILURE")
        self.assertEqual(logged_event["error_message"], "Something went very wrong")
        self.assertEqual(logged_event["error_type"], "ValueError")
        self.assertIn("error_stacktrace", logged_event)
        self.assertTrue(len(logged_event["error_stacktrace"]) > 0)

    async def test_resource_id_extraction_from_kwargs(self):
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS")
        async def mock_op_with_ids(sample_id: str, user_id: str, request: Request): # sample_id should be picked first
            return "ok"

        await mock_op_with_ids(sample_id="sample1", user_id="user1", request=self.mock_request)
        logged_event = self.mock_logger_service.log.call_args[0][0]
        self.assertIn("sample1", logged_event["target_resource_ids"])
        self.assertNotIn("user1", logged_event["target_resource_ids"]) # Only first one from preferred list

    async def test_input_args_summary_sensitive_field_exclusion(self):
        # This test focuses on the input_args_summary, not data_changed_summary's schema extraction
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS")
        async def mock_op_with_sensitive_args(request: Request, password: str, token: str, normal_arg: str):
            return "ok"

        await mock_op_with_sensitive_args(request=self.mock_request, password="test_password", token="test_token", normal_arg="visible")
        logged_event = self.mock_logger_service.log.call_args[0][0]
        
        summary = logged_event["input_args_summary"]
        self.assertNotIn("password", summary)
        self.assertNotIn("token", summary)
        self.assertEqual(summary["normal_arg"], "visible")

    async def test_no_logger_service_available(self):
        # Detach logger service from request mock
        self.mock_request.app.state.activity_logger_service = None 
        
        @log_activity(success_event_type="MOCK_OPERATION_SUCCESS")
        async def mock_operation(request: Request):
            return "success"
        
        # Should run without error and without calling log
        with patch('builtins.print') as mock_print: # To check for the warning
            result = await mock_operation(request=self.mock_request)
            self.assertEqual(result, "success")
            self.mock_logger_service.log.assert_not_called()
            mock_print.assert_any_call("Warning: ActivityLoggerService not found for event MOCK_OPERATION_SUCCESS. Operation will proceed without logging.")

    async def test_sync_function_decoration_basic_call(self):
        # Note: The sync wrapper in PoC is very basic and might not find logger_service
        # This test primarily checks if it wraps without error and calls the original function.
        
        # For this test, let's mock the global singleton access if the sync wrapper tries it
        mock_sync_logger_instance = MagicMock(spec=ActivityLoggerService)
        mock_sync_logger_instance.log = MagicMock()

        @log_activity(success_event_type="MOCK_SYNC_SUCCESS", failure_event_type="MOCK_SYNC_FAILURE")
        def mock_sync_operation(value: int):
            if value < 0:
                raise ValueError("Sync negative value")
            return f"Sync result: {value}"

        with patch('utils.activity_logging_decorators.ActivityLoggerService', return_value=mock_sync_logger_instance) as MockGlobalLogger:
            # Test success
            result_success = mock_sync_operation(value=10)
            self.assertEqual(result_success, "Sync result: 10")
            mock_sync_logger_instance.log.assert_called_once()
            logged_event_success = mock_sync_logger_instance.log.call_args[0][0]
            self.assertEqual(logged_event_success["event_type"], "MOCK_SYNC_SUCCESS")

            mock_sync_logger_instance.log.reset_mock() # Reset for next call

            # Test failure
            with self.assertRaises(ValueError):
                mock_sync_operation(value=-5)
            
            mock_sync_logger_instance.log.assert_called_once()
            logged_event_failure = mock_sync_logger_instance.log.call_args[0][0]
            self.assertEqual(logged_event_failure["event_type"], "MOCK_SYNC_FAILURE")
            self.assertEqual(logged_event_failure["error_message"], "Sync negative value")
            self.assertEqual(logged_event_failure["error_type"], "ValueError")
            self.assertIn("error_stacktrace", logged_event_failure)


if __name__ == '__main__':
    unittest.main()

# Ensure the test file ends with a newline
