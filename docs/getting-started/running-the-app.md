# Running the Application

This guide explains how to run the My Platform application after you have successfully completed the [Installation Guide](installation.md).

## Prerequisites

Before running the application, ensure that:

1.  **Installation is Complete**: All steps from the [Installation Guide](installation.md) have been followed.
2.  **Virtual Environment is Activated**: If you set up a virtual environment (recommended), make sure it's active.
    -   macOS/Linux: `source venv/bin/activate`
    -   Windows: `.\venv\Scripts\activate`
3.  **Required Services are Running**:
    -   **Database**: The database server (e.g., PostgreSQL) must be running and accessible, as configured in your `.env` file. If using Docker, ensure the database container is up (e.g., `docker-compose ps`).
    -   **Other Services (If applicable)**: If your application relies on other services like Redis for caching, Kafka for streaming, etc., ensure they are also running.

## Running the FastAPI Application

The application is typically run using an ASGI server like Uvicorn. The main application instance is usually found in `main.py`.

**Command to Start the Server:**

From the project root directory, run the following command:

```bash
uvicorn main:app --reload
```

Let's break down this command:
-   `uvicorn`: The ASGI server.
-   `main:app`:
    -   `main` refers to the Python file `main.py`.
    -   `app` refers to the FastAPI application instance created within `main.py` (e.g., `app = FastAPI()`).
-   `--reload`: This flag enables auto-reloading. Uvicorn will watch for changes in your code and automatically restart the server. This is very useful for development. For production, you would typically not use `--reload`.

**Host and Port:**

By default, Uvicorn will start the server on:
-   **Host**: `127.0.0.1` (localhost)
-   **Port**: `8000`

So, the application will typically be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

You might see output similar to this in your terminal:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using statreload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Accessing the Application

-   **Main Application**: Open your web browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) (or the configured host/port). The behavior here depends on whether you have frontend routes defined or just API routes.

## Accessing API Documentation

FastAPI automatically generates interactive API documentation. You can access them at:

-   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    -   This interface allows you to explore all API endpoints, view their schemas (request/response models), and even try them out directly in your browser.
-   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
    -   This provides an alternative, often cleaner, documentation view.

## Troubleshooting

-   **Port Already in Use**: If you get an error that port 8000 is already in use, another application might be using it. You can either stop that application or run Uvicorn on a different port:
    ```bash
    uvicorn main:app --reload --port 8001
    ```
-   **Module Not Found Errors**: Ensure your virtual environment is active and all dependencies from `requirements.txt` are installed.
-   **Database Connection Errors**: Double-check your `.env` file settings for the database and ensure the database server is running and accessible. Verify that migrations have been applied (`alembic upgrade head`).

## Stopping the Server

To stop the Uvicorn server, press `CTRL+C` in the terminal where it's running.
