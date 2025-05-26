import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException # For testing specific exception handling

# Adjust import path based on your project structure
from middleware.activity_logging_middleware import ActivityLoggingMiddleware
from services.activity_logger_service import ActivityLoggerService # For type hint

# Ensure the middleware directory is in the Python path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestActivityLoggingMiddleware(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Mock the ActivityLoggerService that the middleware will instantiate
        self.mock_logger_service_instance = MagicMock(spec=ActivityLoggerService)
        self.mock_logger_service_instance.log = MagicMock() # Mock the log method

        # Patch the ActivityLoggerService where it's imported by the middleware module
        self.activity_logger_patcher = patch('middleware.activity_logging_middleware.ActivityLoggerService')
        self.MockActivityLoggerServiceClass = self.activity_logger_patcher.start()
        self.MockActivityLoggerServiceClass.return_value = self.mock_logger_service_instance
        
        # Dummy app object for middleware instantiation
        self.dummy_app = MagicMock() 
        self.middleware = ActivityLoggingMiddleware(app=self.dummy_app)

    async def asyncTearDown(self):
        self.activity_logger_patcher.stop()

    async def test_successful_request_logging(self):
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/test/path"
        mock_request.headers = {
            "user-agent": "TestAgent/1.0",
            "referer": "http://example.com",
            "origin": "http://example.com",
            "accept-language": "en-US,en;q=0.9",
            "accept-encoding": "gzip, deflate",
            "accept": "application/json",
            "x-forwarded-for": "1.2.3.4", # Example of another header
        }
        mock_request.state = MagicMock() # Ensure state exists
        mock_request.state.user = MagicMock(email="test@example.com", id="user_123")

        # Mock call_next to simulate request processing
        mock_response_content = {"message": "success"}
        mock_call_next_response = JSONResponse(content=mock_response_content, status_code=200)
        call_next_func = AsyncMock(return_value=mock_call_next_response)

        # Dispatch the request through the middleware
        response = await self.middleware.dispatch(mock_request, call_next_func)

        # Assertions
        call_next_func.assert_called_once_with(mock_request)
        self.assertEqual(response.status_code, 200)
        response_body = b""
        async for chunk in response.body_iterator: # Iterate over async generator
            response_body += chunk
        self.assertEqual(json.loads(response_body.decode()), mock_response_content)


        self.mock_logger_service_instance.log.assert_called_once()
        logged_event = self.mock_logger_service_instance.log.call_args[0][0]
        
        self.assertEqual(logged_event["event_type"], "REQUEST_RESPONSE_CYCLE")
        self.assertEqual(logged_event["user_email"], "test@example.com")
        self.assertEqual(logged_event["request_ip_address"], "127.0.0.1")
        self.assertEqual(logged_event["request_method"], "GET")
        self.assertEqual(logged_event["request_path"], "/test/path")
        self.assertEqual(logged_event["response_status_code"], 200)
        self.assertIn("response_time_ms", logged_event)

        # Test fingerprinting headers
        fingerprint = logged_event["request_fingerprint_headers"]
        self.assertEqual(fingerprint["user-agent"], "TestAgent/1.0")
        self.assertEqual(fingerprint["referer"], "http://example.com")
        self.assertEqual(fingerprint["origin"], "http://example.com")
        self.assertEqual(fingerprint["accept-language"], "en-US,en;q=0.9")
        self.assertEqual(fingerprint["accept-encoding"], "gzip, deflate")
        self.assertEqual(fingerprint["accept"], "application/json")
        self.assertEqual(fingerprint["x-forwarded-for"], "1.2.3.4")
        self.assertEqual(fingerprint["x-real-ip"], "unknown") # Not present in mock_request.headers

    async def test_unhandled_exception_logging(self):
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock(); mock_request.client.host = "127.0.0.1"
        mock_request.method = "POST"; mock_request.url = MagicMock(); mock_request.url.path = "/error/path"
        mock_request.headers = {"user-agent": "ErrorAgent/1.0"}
        mock_request.state = MagicMock(); mock_request.state.user = None # Anonymous user

        # Simulate call_next raising a generic exception
        call_next_func = AsyncMock(side_effect=ValueError("Something broke badly"))

        # Dispatch the request
        response = await self.middleware.dispatch(mock_request, call_next_func)

        # Assertions
        call_next_func.assert_called_once_with(mock_request)
        self.assertEqual(response.status_code, 500) # Should return a generic 500
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        self.assertEqual(json.loads(response_body.decode()), {"detail": "Internal Server Error"})

        self.mock_logger_service_instance.log.assert_called_once()
        logged_event = self.mock_logger_service_instance.log.call_args[0][0]

        self.assertEqual(logged_event["event_type"], "UNHANDLED_EXCEPTION")
        self.assertEqual(logged_event["user_email"], "anonymous") # User not set on state
        self.assertEqual(logged_event["response_status_code"], 500)
        self.assertEqual(logged_event["error_type"], "ValueError")
        self.assertEqual(logged_event["error_message"], "Something broke badly")
        self.assertIn("error_stacktrace", logged_event)
        self.assertTrue(len(logged_event["error_stacktrace"]) > 0)
        self.assertEqual(logged_event["request_fingerprint_headers"]["user-agent"], "ErrorAgent/1.0")

    async def test_http_exception_reraised(self):
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock(); mock_request.client.host = "127.0.0.1"
        mock_request.method = "PUT"; mock_request.url = MagicMock(); mock_request.url.path = "/http-error"
        mock_request.headers = {}
        mock_request.state = MagicMock(); mock_request.state.user = None

        # Simulate call_next raising an HTTPException
        http_exception_to_raise = HTTPException(status_code=403, detail="Forbidden access")
        call_next_func = AsyncMock(side_effect=http_exception_to_raise)

        # Dispatch the request and assert HTTPException is re-raised
        with self.assertRaises(HTTPException) as context:
            await self.middleware.dispatch(mock_request, call_next_func)
        
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Forbidden access")

        # Verify no UNHANDLED_EXCEPTION log was made (as HTTPException should be handled by FastAPI)
        # The current middleware code re-raises HTTPException *without* logging it itself.
        # If the requirement was to log HTTPExceptions in middleware too, this test would change.
        self.mock_logger_service_instance.log.assert_not_called() 

    async def test_user_extraction_from_state_after_call_next(self):
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock(); mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"; mock_request.url = MagicMock(); mock_request.url.path = "/user-test"
        mock_request.headers = {}
        
        # Simulate request.state.user being populated *during* call_next (by another middleware/auth)
        mock_request.state = MagicMock()
        # Initially, no user on state
        if hasattr(mock_request.state, 'user'): # Ensure it's clear user is not set
            del mock_request.state.user 

        async def call_next_side_effect(request_arg):
            # Simulate user being set on state during downstream processing
            request_arg.state.user = MagicMock(email="user_set_downstream@example.com", id="user_downstream_id")
            return JSONResponse(content={"message": "user processed"}, status_code=200)

        call_next_func = AsyncMock(side_effect=call_next_side_effect)

        await self.middleware.dispatch(mock_request, call_next_func)
        
        self.mock_logger_service_instance.log.assert_called_once()
        logged_event = self.mock_logger_service_instance.log.call_args[0][0]
        
        self.assertEqual(logged_event["user_email"], "user_set_downstream@example.com")


if __name__ == '__main__':
    # Required for JSONResponse body iteration in tests if run directly (though typically run via test runner)
    import json 
    unittest.main()

# Ensure the test file ends with a newline
