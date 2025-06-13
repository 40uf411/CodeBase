# FastAPI Boilerplate Project

## Project Overview

This project serves as a boilerplate/template for FastAPI applications, providing a robust starting point for building modern web services. It includes pre-configured components for authentication, database integration with PostgreSQL, Alembic for database migrations, DragonFlyDB for caching, JWT-based authentication, and Google OAuth integration.

Key Features:
*   **FastAPI:** High-performance web framework for building APIs.
*   **PostgreSQL:** Powerful open-source relational database.
*   **Alembic:** Database migration tool for SQLAlchemy.
*   **DragonFlyDB:** In-memory data store for caching.
*   **JWT Authentication:** Secure token-based authentication.
*   **Google OAuth:** Integration with Google for social login.
*   **SQLAlchemy:** Python SQL toolkit and Object Relational Mapper (ORM).
*   **Pydantic:** Data validation and settings management.
*   **Kafka & WebSockets:** For real-time data streaming.

## Setup Instructions

### Prerequisites

*   Python 3.8 or higher
*   pip (Python package installer)
*   Docker (recommended for running PostgreSQL and DragonFlyDB)

### Cloning the Repository

```bash
git clone <your-repository-url>
cd <repository-directory>
```

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Environment Variables

Application configuration is managed via `core/config.py` and can be overridden by creating a `.env` file in the project root.

Create a `.env` file and add the following critical environment variables:

```env
# PostgreSQL Configuration
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_SERVER=localhost # Or your Docker container name/IP
POSTGRES_PORT=5432

# DragonFlyDB (Cache) Configuration
CACHE_HOST=localhost # Or your Docker container name/IP
CACHE_PORT=6379
CACHE_PASSWORD= # Optional, if your cache requires a password

# JWT Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key # Should be a strong, random string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Application Settings
DEBUG=True # Set to False in production
API_V1_STR="/api/v1"
```
**Note:** For production, ensure `DEBUG` is set to `False` and use strong, unique values for secrets.

### Database Setup

This project uses Alembic for managing database migrations.

**1. Initialize Migrations (if starting from scratch and `alembic/versions` is empty):**
   If you are setting up the database for the first time with no existing tables or migration scripts, you might need to ensure your database is created in PostgreSQL. Then, generate an initial migration:
   ```bash
   alembic revision --autogenerate -m "Initial create all tables"
   ```

**2. Apply Migrations:**
   To apply the latest migrations to your database:
   ```bash
   alembic upgrade head
   ```

The application, when `DEBUG=True` in `core/config.py` (or your `.env` file), may also attempt to create database tables on startup if they don't exist. However, relying on Alembic for schema management is recommended.

### Cache Setup

DragonFlyDB is used for caching. Ensure your DragonFlyDB instance is running and accessible. Configuration is managed via `CACHE_HOST`, `CACHE_PORT`, and `CACHE_PASSWORD` environment variables in your `.env` file or directly in `core/config.py`.

## Running the Application

To run the FastAPI development server:

```bash
uvicorn main:app --reload --host localhost --port 8000
```

The application will be accessible at `http://localhost:8000`.

## Running Tests

(Test setup and commands to be added. Currently, `tests/e2e.py` exists but specific instructions for running tests need to be defined.)
For now, you can try running pytest if it's configured:
```bash
pytest tests/
```

## Project Structure

*   `alembic/`: Database migration scripts managed by Alembic.
*   `alembic.ini`: Configuration file for Alembic.
*   `cache/`: Integration with DragonFlyDB for caching.
    *   `cache.py`: Caching client setup.
*   `core/`: Core application settings, database connection, and authentication logic.
    *   `config.py`: Application configuration and settings management (Pydantic).
    *   `database.py`: SQLAlchemy database engine and session setup.
    *   `security.py`: JWT token generation and validation, password hashing.
*   `main.py`: FastAPI application entry point, including router setup and middleware.
*   `middleware/`: Custom middleware for the application.
    *   `current_user.py`: Middleware to manage the current user context.
*   `models/`: SQLAlchemy database models (definitions of database tables).
    *   `user_model.py`: User model example.
*   `oauths/`: OAuth integration logic.
    *   `google.py`: Google OAuth client and authentication flow.
*   `repositories/`: Data Access Layer, responsible for database interactions.
    *   `base_repository.py`: Base repository with common CRUD operations.
    *   `user_repository.py`: Repository for user data.
*   `routers/`: API endpoint definitions (FastAPI routers).
    *   `auth_router.py`: Authentication related endpoints (login, signup, Google OAuth).
    *   `health_check_router.py`: Endpoint for health checks.
    *   `user_router.py`: User-related API endpoints.
*   `schemas/`: Pydantic schemas for request/response validation and data serialization.
    *   `auth_schema.py`: Schemas for authentication requests and responses.
    *   `user_schema.py`: Schemas for user data.
    *   `utils_schema.py`: Common utility schemas (e.g., for messages).
*   `services/`: Business logic layer, orchestrating operations between routers and repositories.
    *   `auth_service.py`: Service for authentication logic.
    *   `user_service.py`: Service for user-related business logic.
*   `streaming/`: Kafka and WebSocket integration for real-time communication.
    *   `kafka_consumer.py`: Kafka consumer setup.
    *   `kafka_producer.py`: Kafka producer setup.
    *   `websockets.py`: WebSocket connection management.
*   `tests/`: Test files.
    *   `e2e.py`: End-to-end tests (example).
*   `utils/`: Utility modules and helper functions.
    *   `common.py`: Common utility functions.
    *   `ecs_logging.py`: Logging setup (e.g., for ECS).
    *   `token_bucket.py`: Implementation of a token bucket algorithm for rate limiting.
*   `requirements.txt`: List of Python dependencies.
*   `.env.example`: Example environment file (though not explicitly present, this is a good practice to add).
*   `readme.md`: This file.

## Activity Logging
The application features a comprehensive and configurable activity logging system that records detailed information about user actions, system events, and errors. This is crucial for security auditing, troubleshooting, and monitoring platform activity.

For detailed information on log format, storage, configuration, and key event types, please see [LOGGING.md](./LOGGING.md).

## Containerization (Docker)

### Building the Docker Image Locally
To build the Docker image for this application locally, navigate to the project root directory (where the `Dockerfile` is located) and run:
```bash
docker build -t <your-image-name> .
```
Replace `<your-image-name>` with a name you want to give your image (e.g., `my-fastapi-app`).

### Running the Docker Container Locally
To run the built image as a container:
```bash
docker run -p 8000:8000 \
  -e SQLALCHEMY_DATABASE_URI="postgresql://user:password@host:port/dbname" \
  -e JWT_SECRET_KEY="your-super-secret-key" \
  -e DEBUG="False" \
  # Add other necessary environment variables as per your application's config.py
  <your-image-name>
```
Make sure to:
- Replace `<your-image-name>` with the name you used during the build.
- Set appropriate values for `SQLALCHEMY_DATABASE_URI`, `JWT_SECRET_KEY`, and any other required environment variables. The application inside the container relies on these for its configuration.
- The application will be accessible at `http://localhost:8000`.

**Important:** The Docker image expects all necessary configurations (database URLs, secret keys, etc.) to be provided via environment variables at runtime. Refer to `core/config.py` for required variables. Do not hardcode sensitive information directly in the `Dockerfile` or commit it to version control.

## CI Pipeline
This project uses GitHub Actions for Continuous Integration (CI). The CI pipeline is defined in `.github/workflows/main.yml` and automates several quality checks and build processes.

**Key Stages:**
The pipeline typically includes the following stages:
1.  **Lint & Format Check:** Ensures code style consistency using Flake8 and Black.
2.  **Unit Tests:** Runs fast, isolated tests for individual components.
3.  **Integration Tests:** Performs tests involving interactions between components, using service containers for PostgreSQL and Redis to simulate a live environment. Database migrations (Alembic) are applied before these tests.
4.  **Security Scans:** Includes checks for potential security vulnerabilities in code (Bandit) and dependencies (pip-audit).
5.  **Build Docker Image:** Builds a Docker container image of the application.
6.  **Push Docker Image (Conditional):** On pushes to the `main` branch, the built Docker image is pushed to the GitHub Container Registry (GHCR).

**Triggers:**
The CI pipeline is automatically triggered on:
- Pushes to the `main` branch.
- Pull requests targeting the `main` branch.

You can view the status and logs of CI runs in the "Actions" tab of the GitHub repository.

## Contributing

If this were an open project, contributions would be welcome! Please follow these general guidelines:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring code is well-formatted and includes tests where applicable.
4.  Commit your changes (`git commit -am 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Create a new Pull Request.

---

*This README provides a comprehensive guide to understanding, setting up, and running the FastAPI boilerplate project.*
