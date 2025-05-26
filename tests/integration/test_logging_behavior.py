import pytest
import json
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting db fixture

# Assuming conftest.py provides client, db, admin_user_headers, log_capture
from models.user import User # For checking DB directly if needed

API_V1_STR = "/api/v1"
AUTH_LOGIN_ENDPOINT = f"{API_V1_STR}/auth/login"
USERS_ENDPOINT = f"{API_V1_STR}/users/"
ADMIN_LOGGING_SETTINGS_ENDPOINT = f"{API_V1_STR}/admin/logging-settings"

# Helper to parse captured JSON logs
def parse_log_json(log_stream_value: str):
    logs = []
    for line in log_stream_value.strip().split('\n'):
        if line:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON log line: {line}")
    return logs

class TestLoggingBehavior:

    def test_auth_login_success_logging_toggle(
        self, client: TestClient, db: Session, admin_user_headers: dict, log_capture, # log_capture fixture from conftest
        # We need a test user to login with
    ):
        log_stream = log_capture # log_stream is the io.StringIO from the fixture

        # Create a temporary user for login tests if one doesn't exist from headers
        test_login_email = "login_test_user@example.com"
        test_login_password = "testloginpassword"
        
        user = db.query(User).filter(User.email == test_login_email).first()
        if not user:
            from core.security import get_password_hash # Assuming this is accessible
            user_create_payload = {
                "email": test_login_email,
                "password": test_login_password, # This user is created directly, not via API here
                "full_name": "Login Test User",
                "is_active": True,
                "is_superuser": False
            }
            # To use AuthService to create user (if preferred over direct model manipulation)
            # auth_service = AuthService(db=db) # auth_service might need request if decorated
            # For simplicity in fixture, direct model creation or non-decorated service method used
            new_user = User(
                email=user_create_payload["email"],
                hashed_password=get_password_hash(user_create_payload["password"]),
                full_name=user_create_payload["full_name"],
                is_active=user_create_payload["is_active"],
                is_superuser=user_create_payload["is_superuser"]
            )
            db.add(new_user)
            db.commit()
        
        login_payload = {"username": test_login_email, "password": test_login_password}

        # --- Scenario 1: Ensure AUTH_LOGIN_SUCCESS is enabled (default) and test login ---
        # Optional: Explicitly set to True if default might change or for test clarity
        client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/AUTH_LOGIN_SUCCESS", json={"is_enabled": True}, headers=admin_user_headers)
        
        response_login1 = client.post(AUTH_LOGIN_ENDPOINT, data=login_payload)
        assert response_login1.status_code == status.HTTP_200_OK
        
        logs1 = parse_log_json(log_stream.getvalue())
        login_success_logs1 = [log for log in logs1 if log["message"].get("event_type") == "USER_LOGIN_SUCCESS"]
        assert len(login_success_logs1) >= 1, "USER_LOGIN_SUCCESS event should be logged when enabled."
        assert login_success_logs1[-1]["message"]["email_attempted"] == test_login_email
        
        # Clear the stream for the next part of the test
        log_stream.truncate(0)
        log_stream.seek(0)

        # --- Scenario 2: Disable AUTH_LOGIN_SUCCESS and test login ---
        put_response = client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/AUTH_LOGIN_SUCCESS", json={"is_enabled": False}, headers=admin_user_headers)
        assert put_response.status_code == status.HTTP_200_OK
        
        response_login2 = client.post(AUTH_LOGIN_ENDPOINT, data=login_payload)
        assert response_login2.status_code == status.HTTP_200_OK
        
        logs2 = parse_log_json(log_stream.getvalue())
        login_success_logs2 = [log for log in logs2 if log["message"].get("event_type") == "USER_LOGIN_SUCCESS"]
        assert len(login_success_logs2) == 0, "USER_LOGIN_SUCCESS event should NOT be logged when disabled."

        # Cleanup: Re-enable AUTH_LOGIN_SUCCESS (optional, good practice)
        client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/AUTH_LOGIN_SUCCESS", json={"is_enabled": True}, headers=admin_user_headers)


    def test_log_data_modifications_for_user_create(
        self, client: TestClient, admin_user_headers: dict, log_capture
    ):
        log_stream = log_capture
        user_create_api_event_type = "USER_CREATE_VIA_API_SUCCESS" # From user_router decorator

        # Ensure USER_CREATE_VIA_API_SUCCESS is enabled (it should be by default if not explicitly set otherwise)
        # For robustness, can explicitly enable it:
        client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/{user_create_api_event_type}", json={"is_enabled": True}, headers=admin_user_headers)


        # --- Scenario 1: LOG_DATA_MODIFICATIONS is disabled ---
        put_resp_log_data_mod_disable = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/LOG_DATA_MODIFICATIONS", 
            json={"is_enabled": False}, 
            headers=admin_user_headers
        )
        assert put_resp_log_data_mod_disable.status_code == status.HTTP_200_OK

        user_payload1 = {
            "email": "logdatatest1@example.com", "password": "password123", 
            "full_name": "Log Data Test User 1"
        }
        response_create1 = client.post(USERS_ENDPOINT, json=user_payload1, headers=admin_user_headers) # Use admin to create user
        assert response_create1.status_code == status.HTTP_201_CREATED
        
        logs1 = parse_log_json(log_stream.getvalue())
        create_user_logs1 = [log for log in logs1 if log["message"].get("event_type") == user_create_api_event_type]
        assert len(create_user_logs1) >= 1
        # data_changed_summary should be absent or minimal (current decorator doesn't add it if LOG_DATA_MODIFICATIONS is False)
        assert "data_changed_summary" not in create_user_logs1[-1]["message"], \
            "data_changed_summary should be absent when LOG_DATA_MODIFICATIONS is False."

        log_stream.truncate(0); log_stream.seek(0) # Clear stream

        # --- Scenario 2: LOG_DATA_MODIFICATIONS is enabled ---
        put_resp_log_data_mod_enable = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/LOG_DATA_MODIFICATIONS", 
            json={"is_enabled": True}, 
            headers=admin_user_headers
        )
        assert put_resp_log_data_mod_enable.status_code == status.HTTP_200_OK

        user_payload2 = {
            "email": "logdatatest2@example.com", "password": "password456",
            "full_name": "Log Data Test User 2"
        }
        response_create2 = client.post(USERS_ENDPOINT, json=user_payload2, headers=admin_user_headers)
        assert response_create2.status_code == status.HTTP_201_CREATED
        created_user_id2 = response_create2.json()["id"]

        logs2 = parse_log_json(log_stream.getvalue())
        create_user_logs2 = [log for log in logs2 if log["message"].get("event_type") == user_create_api_event_type]
        assert len(create_user_logs2) >= 1
        
        last_log_message = create_user_logs2[-1]["message"]
        assert "data_changed_summary" in last_log_message, \
            "data_changed_summary should be present when LOG_DATA_MODIFICATIONS is True."
        
        summary = last_log_message["data_changed_summary"]
        assert "input_data" in summary
        assert summary["input_data"]["email"] == user_payload2["email"]
        assert "password" not in summary["input_data"] # Sensitive field check
        assert summary["created_resource_id"] == created_user_id2

        # Cleanup: Disable LOG_DATA_MODIFICATIONS
        client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/LOG_DATA_MODIFICATIONS", json={"is_enabled": False}, headers=admin_user_headers)

# Ensure the test file ends with a newline.
