import pytest
import json
from fastapi import status, Request, HTTPException, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock # For mocking service calls

# Assuming conftest.py provides client, db, admin_user_headers, log_capture
from models.user import User # For type hinting or direct interaction if needed

API_V1_STR = "/api/v1" # Or from settings

# Helper to parse captured JSON logs (can be moved to conftest if used by multiple test files)
def parse_log_json(log_stream_value: str):
    logs = []
    for line in log_stream_value.strip().split('\n'):
        if line:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON log line: {line}")
    return logs

class TestAdvancedLogging:

    # --- 3. Tests for Error Logging ---

    def test_unhandled_exception_in_middleware(
        self, client: TestClient, log_capture, admin_user_headers: dict
    ):
        # Temporarily add a route that will raise an unhandled exception
        # This is tricky as modifying the app instance (client.app) at runtime for TestClient
        # needs to be done carefully or use a custom app factory for tests.
        # For this PoC, let's assume we can add a route to the app used by the client.
        # A cleaner way is to have a dedicated test app or specific endpoint for this.

        # Simple way for this test: mock a downstream call from a known endpoint
        # to raise an exception before the ActivityLoggingMiddleware's main try-catch finishes.
        # However, the middleware wraps `await call_next(request)`.
        # So, the exception must come from `call_next` or downstream route.
        
        # Let's create a temporary route on the app for this test.
        # This requires access to the `app` instance used by `TestClient`.
        # The `client` fixture in conftest.py has `with TestClient(app) as c: yield c`
        # So, `client.app` is the FastAPI app instance.
        
        temp_app = client.app
        original_routes = temp_app.routes[:] # Store original routes

        @temp_app.get("/_test_unhandled_exception_route")
        async def _temp_route_unhandled_error():
            raise ValueError("This is a deliberate unhandled error for testing middleware.")

        # Rebuild router to include the new route. This is important.
        temp_app.router.routes.append(_temp_route_unhandled_error.routes[0])

        log_stream = log_capture
        
        # Make a call to the temporary error-raising route
        # No specific headers needed unless auth is hit before the error.
        # Assuming this test route does not have auth dependencies for simplicity.
        response = client.get("/_test_unhandled_exception_route") # No API_V1_STR needed as it's a direct route name
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Internal Server Error"} # From middleware's generic response

        logs = parse_log_json(log_stream.getvalue())
        unhandled_exception_logs = [log for log in logs if log["message"].get("event_type") == "UNHANDLED_EXCEPTION"]
        
        assert len(unhandled_exception_logs) >= 1
        last_error_log = unhandled_exception_logs[-1]["message"]
        assert last_error_log["error_type"] == "ValueError"
        assert last_error_log["error_message"] == "This is a deliberate unhandled error for testing middleware."
        assert "error_stacktrace" in last_error_log
        assert "Traceback (most recent call last)" in last_error_log["error_stacktrace"]
        assert "_test_unhandled_exception_route" in last_error_log["request_path"]

        # Clean up: remove the temporary route
        temp_app.routes = original_routes
        temp_app.router.routes = original_routes # Also reset the router's explicit list


    @patch('services.auth_service.AuthService.create_user', new_callable=AsyncMock) # Mock at service level
    def test_decorated_function_http_exception(
        self, mock_create_user_in_service: AsyncMock, 
        client: TestClient, admin_user_headers: dict, log_capture
    ):
        # Test the @log_activity decorator on routers/user.py's create_user endpoint
        # when the underlying service call results in an HTTPException.
        
        # Configure the mock to raise HTTPException
        http_exception_detail = "Simulated User Creation Not Allowed"
        mock_create_user_in_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=http_exception_detail
        )
        
        log_stream = log_capture
        user_payload = {"email": "decorator_http_fail@example.com", "password": "password", "full_name": "Test"}

        response = client.post(f"{API_V1_STR}/users/", json=user_payload, headers=admin_user_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == http_exception_detail

        logs = parse_log_json(log_stream.getvalue())
        # The decorator on the router endpoint `routers.user.create_user` should log this.
        # Event type from decorator: USER_CREATE_VIA_API_FAILURE
        failure_logs = [log for log in logs if log["message"].get("event_type") == "USER_CREATE_VIA_API_FAILURE"]
        assert len(failure_logs) >= 1
        
        last_failure_log_msg = failure_logs[-1]["message"]
        assert last_failure_log_msg["error_message"] == http_exception_detail
        assert last_failure_log_msg["status_code"] == status.HTTP_403_FORBIDDEN
        assert "error_stacktrace" not in last_failure_log_msg # Decorator does not add stack for HTTPException by default

    @patch('services.auth_service.AuthService.create_user', new_callable=AsyncMock)
    def test_decorated_function_general_exception(
        self, mock_create_user_in_service: AsyncMock,
        client: TestClient, admin_user_headers: dict, log_capture
    ):
        # Test the @log_activity decorator on routers/user.py's create_user endpoint
        # when the underlying service call results in a non-HTTP generic Exception.
        
        general_error_message = "Simulated critical service failure"
        mock_create_user_in_service.side_effect = TypeError(general_error_message) # Example non-HTTP error
        
        log_stream = log_capture
        user_payload = {"email": "decorator_general_fail@example.com", "password": "password", "full_name": "Test"}

        response = client.post(f"{API_V1_STR}/users/", json=user_payload, headers=admin_user_headers)
        
        # The decorator catches the exception and re-raises it.
        # The middleware should then catch this and return a 500.
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        # The response detail will be generic if middleware caught it.
        # If decorator re-raises and something else catches it, this might differ.
        # Based on current decorator, it re-raises. So middleware handles final response.
        assert response.json() == {"detail": "Internal Server Error"}


        logs = parse_log_json(log_stream.getvalue())
        
        # Log from the decorator for the function failure
        decorator_failure_logs = [log for log in logs if log["message"].get("event_type") == "USER_CREATE_VIA_API_FAILURE"]
        assert len(decorator_failure_logs) >= 1
        decorator_log_msg = decorator_failure_logs[-1]["message"]
        assert decorator_log_msg["error_type"] == "TypeError"
        assert decorator_log_msg["error_message"] == general_error_message
        assert "error_stacktrace" in decorator_log_msg
        
        # Log from the middleware for the unhandled exception (if decorator re-raised it fully)
        # The middleware's UNHANDLED_EXCEPTION log should also be present because the decorator re-raises.
        middleware_error_logs = [log for log in logs if log["message"].get("event_type") == "UNHANDLED_EXCEPTION"]
        assert len(middleware_error_logs) >= 1, "Middleware should log the re-raised exception from decorator."
        middleware_log_msg = middleware_error_logs[-1]["message"]
        assert middleware_log_msg["error_type"] == "TypeError" # The original error type
        assert middleware_log_msg["error_message"] == general_error_message


    # --- 4. Tests for Fingerprinting Headers ---
    def test_fingerprinting_headers_logged(self, client: TestClient, log_capture):
        log_stream = log_capture
        
        custom_headers = {
            "User-Agent": "IntegrationTestAgent/2.0",
            "Referer": "http://integration-test.com/referrer",
            "Origin": "http://integration-test.com",
            "Accept-Language": "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5",
            "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
            "X-Custom-Test-Header": "ThisShouldNotBeLoggedByDefault" # Example of a non-standard header
        }

        # Use a simple, known-good endpoint that goes through the middleware
        # The /health endpoint is defined in main.py and doesn't require auth
        response = client.get(f"{API_V1_STR}/health", headers=custom_headers) # Assuming /health is under API_V1_STR
        if response.status_code == status.HTTP_404_NOT_FOUND: # Fallback if /health isn't under version prefix
             response = client.get("/health", headers=custom_headers)
        
        assert response.status_code == status.HTTP_200_OK

        logs = parse_log_json(log_stream.getvalue())
        request_cycle_logs = [log for log in logs if log["message"].get("event_type") == "REQUEST_RESPONSE_CYCLE"]
        assert len(request_cycle_logs) >= 1
        
        last_log_message = request_cycle_logs[-1]["message"]
        assert "request_fingerprint_headers" in last_log_message
        
        fingerprints = last_log_message["request_fingerprint_headers"]
        assert fingerprints["user-agent"] == custom_headers["User-Agent"]
        assert fingerprints["referer"] == custom_headers["Referer"]
        assert fingerprints["origin"] == custom_headers["Origin"]
        assert fingerprints["accept-language"] == custom_headers["Accept-Language"]
        assert fingerprints["x-forwarded-for"] == custom_headers["X-Forwarded-For"]
        assert fingerprints["x-real-ip"] == "unknown" # As it wasn't in custom_headers
        assert "x-custom-test-header" not in fingerprints # Not part of the logged set by default

# Ensure the test file ends with a newline.
