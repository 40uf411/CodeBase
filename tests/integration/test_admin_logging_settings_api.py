import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Assuming your conftest.py sets up the app, client, db, and user headers correctly.
# Also assumes AdminLoggingSetting model and default settings are available.
from models.admin_logging_setting import AdminLoggingSetting # To interact with DB directly if needed for setup/verify
from sqlalchemy.orm import Session # For type hinting db fixture

# Define the API prefix, e.g., from your settings or main app
API_V1_STR = "/api/v1" # Or settings.API_V1_STR if settings is importable easily
ADMIN_LOGGING_SETTINGS_ENDPOINT = f"{API_V1_STR}/admin/logging-settings"

class TestAdminLoggingSettingsAPI:

    # --- Authentication/Authorization Tests ---
    def test_get_logging_settings_unauthenticated(self, client: TestClient):
        response = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT)
        # Expect 401 or 403 depending on how auth middleware is set up for missing token
        # FastAPI's Depends(oauth2_scheme) usually results in 401 if token is missing.
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 

    def test_get_logging_settings_non_admin_user(self, client: TestClient, regular_user_headers: dict):
        response = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT, headers=regular_user_headers)
        # Expect 403 Forbidden as regular user should not have 'admin:logging_settings:manage'
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_logging_settings_admin_user(self, client: TestClient, admin_user_headers: dict):
        response = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT, headers=admin_user_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        # Check for a few known default settings (names may vary based on your service)
        # These names come from AdminLoggingSettingService.initialize_default_settings
        expected_setting_names = ["AUTH_LOGIN_SUCCESS", "RESOURCE_CREATE", "LOG_DATA_MODIFICATIONS", "REQUEST_RESPONSE_CYCLE"]
        present_setting_names = [item["setting_name"] for item in data]
        for name in expected_setting_names:
            assert name in present_setting_names
        
        log_data_mod_setting = next((item for item in data if item["setting_name"] == "LOG_DATA_MODIFICATIONS"), None)
        assert log_data_mod_setting is not None
        assert log_data_mod_setting["is_enabled"] == False # Default is False

    def test_update_logging_setting_unauthenticated(self, client: TestClient):
        response = client.put(f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/AUTH_LOGIN_SUCCESS", json={"is_enabled": False})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_logging_setting_non_admin_user(self, client: TestClient, regular_user_headers: dict):
        response = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/AUTH_LOGIN_SUCCESS", 
            json={"is_enabled": False}, 
            headers=regular_user_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- PUT Endpoint Tests ---
    def test_update_logging_setting_admin_user(self, client: TestClient, admin_user_headers: dict, db: Session):
        setting_to_test = "AUTH_LOGIN_SUCCESS" # Assuming this is True by default
        
        # 1. Get initial state (optional, but good for context)
        response_get_initial = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT, headers=admin_user_headers)
        initial_settings = {s["setting_name"]: s for s in response_get_initial.json()}
        initial_status = initial_settings[setting_to_test]["is_enabled"]

        # 2. Update the setting (e.g., disable it)
        new_status = not initial_status
        response_put = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/{setting_to_test}",
            json={"is_enabled": new_status},
            headers=admin_user_headers
        )
        assert response_put.status_code == status.HTTP_200_OK
        updated_setting_response = response_put.json()
        assert updated_setting_response["setting_name"] == setting_to_test
        assert updated_setting_response["is_enabled"] == new_status

        # 3. Verify with GET
        response_get_after_put = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT, headers=admin_user_headers)
        settings_after_put = {s["setting_name"]: s for s in response_get_after_put.json()}
        assert settings_after_put[setting_to_test]["is_enabled"] == new_status
        
        # 4. Verify directly in DB (optional, but good for integration confidence)
        db_setting = db.query(AdminLoggingSetting).filter(AdminLoggingSetting.setting_name == setting_to_test).first()
        assert db_setting is not None
        assert db_setting.is_enabled == new_status

        # 5. Change it back to original state (cleanup for this test)
        response_put_back = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/{setting_to_test}",
            json={"is_enabled": initial_status},
            headers=admin_user_headers
        )
        assert response_put_back.status_code == status.HTTP_200_OK
        
        # Verify with GET again
        response_get_after_revert = client.get(ADMIN_LOGGING_SETTINGS_ENDPOINT, headers=admin_user_headers)
        settings_after_revert = {s["setting_name"]: s for s in response_get_after_revert.json()}
        assert settings_after_revert[setting_to_test]["is_enabled"] == initial_status


    def test_update_non_existent_logging_setting(self, client: TestClient, admin_user_headers: dict):
        non_existent_setting_name = "THIS_SETTING_DOES_NOT_EXIST_12345"
        response_put = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/{non_existent_setting_name}",
            json={"is_enabled": True},
            headers=admin_user_headers
        )
        # The API should return 404 if the setting name is not found to be updated.
        assert response_put.status_code == status.HTTP_404_NOT_FOUND
        # Detail message might vary based on router implementation.
        # Example: {"detail": "Logging setting 'THIS_SETTING_DOES_NOT_EXIST_12345' not found."}
        assert "not found" in response_put.json().get("detail", "").lower()


    def test_update_setting_invalid_payload(self, client: TestClient, admin_user_headers: dict):
        setting_to_test = "AUTH_LOGIN_SUCCESS"
        response_put = client.put(
            f"{ADMIN_LOGGING_SETTINGS_ENDPOINT}/{setting_to_test}",
            json={"is_enabled": "not-a-boolean"}, # Invalid payload type
            headers=admin_user_headers
        )
        assert response_put.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Ensure the test file ends with a newline.
