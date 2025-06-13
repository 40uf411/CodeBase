# Microservices Management Platform

This platform provides a web interface for real-time visualization of service load,
starting/stopping/restarting services, and viewing service logs.

## Prerequisites

*   Python 3.7+
*   Access to a terminal or command prompt.

## Setup and Running

There are two main components to run: the example FastAPI microservice and the Flask management web application.

### 1. Running the Example Microservice (`example_service`)

The `example_service` is a FastAPI application that the management platform will monitor and control.

1.  **Navigate to the service directory:**
    ```bash
    cd ../microservices/example_service
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv  # Or python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install its dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the service:**
    ```bash
    python main.py
    ```
    The `example_service` should now be running on `http://localhost:8000`.
    You should see log output in the console and also in `microservices/example_service/logs/example_service.log`.

### 2. Running the Management Web Platform

The management platform is a Flask application.

1.  **Navigate to the management platform directory (if not already there):**
    ```bash
    cd path/to/your/project/microservices-managment
    ```
    (Ensure you are in the `microservices-managment` directory that contains `app.py`)

2.  **Create a virtual environment (recommended, if not using one for the whole project):**
    ```bash
    python3 -m venv venv # Or python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install its dependencies:**
    The platform itself requires Flask and requests. For development and testing, you'll also need pytest and requests-mock.
    ```bash
    # For running the app (if you don't have requirements-dev.txt or want minimal install):
    # pip install Flask requests

    # For development (including running tests, from requirements-dev.txt):
    pip install -r requirements-dev.txt
    ```
    *Note: `requirements-dev.txt` includes Flask and requests, so it's sufficient for development.*

4.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The management platform should now be running on `http://localhost:5000`.
    Open this URL in your web browser.

## Using the Platform

*   The main page will show available services (initially, the `example_service`).
*   You can view health metrics (CPU, memory, disk, status, recent logs) by clicking "Get Health".
*   Use the "Start", "Stop", and "Restart" buttons to (simulate) control the service.
*   An auto-refresh toggle is available to periodically update health information.

## Development Notes

*   The `example_service` (FastAPI) runs on port 8000 by default.
*   The Flask management platform runs on port 5000 by default.
*   Unit tests for the Flask app are in `test_app.py` and can be run with `pytest` from the `microservices-managment` directory (after installing dev dependencies).
    ```bash
    # From the microservices-managment directory:
    pytest
    ```

## Project Structure

```
.
├── microservices/                # Contains individual microservices
│   └── example_service/          # A sample FastAPI microservice
│       ├── main.py               # Service logic
│       ├── requirements.txt
│       ├── Dockerfile
│       └── logs/                 # Log files for this service
│           └── example_service.log
│
└── microservices-managment/      # Flask web platform for management
    ├── app.py                    # Main Flask application
    ├── requirements-dev.txt      # Python dependencies for development/testing
    ├── test_app.py               # Unit tests for the Flask app
    ├── static/                   # Static assets (CSS, JS)
    │   └── css/
    │       └── style.css
    └── templates/                # HTML templates
        ├── base.html
        └── index.html
    └── README.md                 # This file
```
