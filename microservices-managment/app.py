import os
import json
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- Service Discovery ---
# Simplified: Hardcoded list of services.
# In the future, this could scan a directory or read a config file.
KNOWN_SERVICES = [
    {'id': 'example_service', 'url': 'http://localhost:8000', 'name': 'Example Service'},
    # {'id': 'another_service', 'url': 'http://localhost:8001', 'name': 'Another Service'}
]

def discover_services():
    """
    Scans a predefined directory for microservices.
    For now, it returns a hardcoded list.
    """
    # This is where dynamic discovery would go.
    # For example, scanning ../microservices:
    # services_dir = os.path.join(os.path.dirname(__file__), '..', 'microservices')
    # discovered = []
    # if os.path.exists(services_dir):
    #     for item in os.listdir(services_dir):
    #         item_path = os.path.join(services_dir, item)
    #         if os.path.isdir(item_path) and not item.startswith('.'):
    #             # Basic assumption: service ID is folder name, port needs to be configured
    #             # This is a placeholder for a more robust discovery mechanism
    #             port = 8000 # Default/example port, needs actual config
    #             if item == "example_service": # Make sure our example is configured
    #                 discovered.append({'id': item, 'name': item.replace('_', ' ').title(), 'url': f'http://localhost:{port}'})
    # if not discovered: # Fallback to known services if discovery yields nothing
    #     return KNOWN_SERVICES
    # return discovered
    return KNOWN_SERVICES


def get_service_url(service_id):
    """Retrieve the URL for a given service_id."""
    for service in discover_services():
        if service['id'] == service_id:
            return service['url']
    return None

# --- Routes ---
@app.route('/')
def index():
    services = discover_services()
    return render_template('index.html', services=services)

@app.route('/service/<service_id>/health')
def service_health(service_id):
    service_url = get_service_url(service_id)
    if not service_url:
        return jsonify({"error": "Service not found"}), 404

    try:
        response = requests.get(f"{service_url}/health", timeout=5)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return jsonify(response.json())
    except requests.exceptions.Timeout:
        return jsonify({"error": "Service timed out", "service_id": service_id}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Service unreachable", "service_id": service_id}), 503
    except requests.exceptions.HTTPError as e:
        # Try to return the service's error message if possible
        try:
            error_json = e.response.json()
        except ValueError: # Not a JSON response
            error_json = {"error_message": e.response.text}
        return jsonify({"error": "Service returned an error", "service_id": service_id, "status_code": e.response.status_code, "details": error_json}), e.response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e), "service_id": service_id}), 500


@app.route('/service/<service_id>/<action>', methods=['POST'])
def service_control(service_id, action):
    service_url = get_service_url(service_id)
    if not service_url:
        return jsonify({"error": "Service not found"}), 404

    if action not in ['start', 'stop', 'restart']:
        return jsonify({"error": "Invalid action"}), 400

    try:
        response = requests.post(f"{service_url}/{action}", timeout=10) # Longer timeout for control actions
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Action '{action}' timed out", "service_id": service_id}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Service unreachable", "service_id": service_id}), 503
    except requests.exceptions.HTTPError as e:
        try:
            error_json = e.response.json()
        except ValueError:
            error_json = {"error_message": e.response.text}
        return jsonify({"error": f"Action '{action}' failed", "service_id": service_id, "status_code": e.response.status_code, "details": error_json}), e.response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e), "service_id": service_id}), 500


if __name__ == '__main__':
    # Make sure to run on a different port than the example_service
    app.run(debug=True, host='0.0.0.0', port=5000)
