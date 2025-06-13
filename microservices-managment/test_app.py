import pytest
import json
import requests
from app import app as flask_app # flask_app from microservices-managment/app.py

# Configuration for KNOWN_SERVICES in app.py (for test reference)
# KNOWN_SERVICES = [
#     {'id': 'example_service', 'url': 'http://localhost:8000', 'name': 'Example Service'},
# ]
MOCK_SERVICE_ID = "example_service"
MOCK_SERVICE_URL_BASE = "http://localhost:8000" # Must match what's in app.py's KNOWN_SERVICES

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    # If SERVER_NAME is set, url_for can generate external URLs without a request context
    # However, for direct client calls, it's often not strictly necessary.
    # flask_app.config['SERVER_NAME'] = 'localhost:5000'
    with flask_app.test_client() as client:
        yield client

def test_index_page(client):
    """Test the main page loads and contains expected content."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Microservices Management Dashboard" in response.data
    assert MOCK_SERVICE_ID.encode() in response.data # Check if the service ID is rendered

def test_get_health_success(client, requests_mock):
    """Test successful retrieval of health status from a microservice."""
    mock_health_data = {
        "service_name": MOCK_SERVICE_ID,
        "status": "running",
        "cpu_usage_percent": 10.5,
        "memory_usage_percent": 55.2,
        "disk_usage_percent": 30.1,
        "recent_logs": ["log line 1", "log line 2"]
    }
    requests_mock.get(f"{MOCK_SERVICE_URL_BASE}/health", json=mock_health_data, status_code=200)

    response = client.get(f"/service/{MOCK_SERVICE_ID}/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == mock_health_data

def test_get_health_service_error(client, requests_mock):
    """Test handling of a 500 error from the microservice health endpoint."""
    error_detail_from_service = {"error": "Service internal failure"}
    requests_mock.get(f"{MOCK_SERVICE_URL_BASE}/health",
                      json=error_detail_from_service,
                      status_code=500,
                      reason="Internal Server Error")

    response = client.get(f"/service/{MOCK_SERVICE_ID}/health")
    # Based on app.py, it should return the status code from the HTTPError's response
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Service returned an error"
    assert data["service_id"] == MOCK_SERVICE_ID
    assert data["status_code"] == 500
    assert data["details"] == error_detail_from_service

def test_get_health_service_timeout(client, requests_mock):
    """Test handling of a timeout when connecting to microservice health endpoint."""
    requests_mock.get(f"{MOCK_SERVICE_URL_BASE}/health", exc=requests.exceptions.Timeout)

    response = client.get(f"/service/{MOCK_SERVICE_ID}/health")
    assert response.status_code == 504 # Gateway Timeout
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Service timed out"
    assert data["service_id"] == MOCK_SERVICE_ID

def test_get_health_service_connection_error(client, requests_mock):
    """Test handling of a connection error to microservice health endpoint."""
    requests_mock.get(f"{MOCK_SERVICE_URL_BASE}/health", exc=requests.exceptions.ConnectionError)

    response = client.get(f"/service/{MOCK_SERVICE_ID}/health")
    assert response.status_code == 503 # Service Unavailable
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Service unreachable"
    assert data["service_id"] == MOCK_SERVICE_ID

def test_get_health_non_existent_service(client):
    """Test requesting health for a service not in KNOWN_SERVICES."""
    response = client.get("/service/non_existent_service/health")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Service not found"

def test_control_service_action_success(client, requests_mock):
    """Test successful invocation of a control action (e.g., start)."""
    action = "start"
    mock_action_response = {"message": f"{MOCK_SERVICE_ID} {action} initiated.", "current_status": "running"}
    requests_mock.post(f"{MOCK_SERVICE_URL_BASE}/{action}", json=mock_action_response, status_code=200)

    response = client.post(f"/service/{MOCK_SERVICE_ID}/{action}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == mock_action_response

def test_control_service_action_service_error(client, requests_mock):
    """Test handling of an error from the microservice during a control action."""
    action = "stop"
    error_detail_from_service = {"error": "Failed to stop, resource busy"}
    requests_mock.post(f"{MOCK_SERVICE_URL_BASE}/{action}",
                       json=error_detail_from_service,
                       status_code=409,
                       reason="Conflict") # Example error

    response = client.post(f"/service/{MOCK_SERVICE_ID}/{action}")
    assert response.status_code == 409 # Mirroring the service's error status
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == f"Action '{action}' failed"
    assert data["service_id"] == MOCK_SERVICE_ID
    assert data["status_code"] == 409
    assert data["details"] == error_detail_from_service

def test_control_service_invalid_action(client):
    """Test providing an invalid action string to the control route."""
    response = client.post(f"/service/{MOCK_SERVICE_ID}/invalid_action")
    assert response.status_code == 400 # Bad Request
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Invalid action"

def test_control_service_non_existent_service(client):
    """Test control action for a service not in KNOWN_SERVICES."""
    response = client.post("/service/non_existent_service/start")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Service not found"

# Example test for 'restart' action
def test_control_service_restart_success(client, requests_mock):
    action = "restart"
    mock_action_response = {"message": f"{MOCK_SERVICE_ID} {action} initiated.", "current_status": "running"}
    requests_mock.post(f"{MOCK_SERVICE_URL_BASE}/{action}", json=mock_action_response, status_code=200)

    response = client.post(f"/service/{MOCK_SERVICE_ID}/{action}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == mock_action_response
