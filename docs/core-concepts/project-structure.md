# Project Structure

This document outlines the main directories and key files in the My Platform project, providing an overview of where different components are located.

```
my-platform/
├── alembic/                   # Database migration scripts (Alembic)
├── core/                      # Core application components
│   ├── __init__.py
│   ├── auth.py                # Authentication logic, privilege checks
│   ├── config.py              # Configuration management (e.g., from .env)
│   ├── database.py            # Database session, engine setup (SQLAlchemy)
│   ├── exceptions.py          # Custom application exceptions
│   └── security.py            # Security-related utilities (e.g., password hashing)
├── docs/                      # Project documentation (this site)
│   ├── core-concepts/
│   ├── features/
│   ├── getting-started/
│   ├── ...
│   └── index.md
├── models/                    # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base.py                # Base model class (e.g., with common ID, timestamps)
│   ├── user.py
│   ├── role.py
│   ├── privilege.py
│   └── ... (other entity models)
├── repositories/              # Data Access Layer (Repository pattern)
│   ├── __init__.py
│   ├── base_repository.py     # Base repository class with common CRUD operations
│   ├── user_repository.py
│   └── ... (other entity repositories)
├── routers/                   # FastAPI routers and API endpoint definitions
│   ├── __init__.py
│   ├── auth.py                # Authentication related endpoints (login, tokens)
│   ├── user.py
│   └── ... (other entity routers)
├── schemas/                   # Pydantic schemas for data validation and serialization
│   ├── __init__.py
│   ├── base.py                # Base schema classes
│   ├── user.py                # User related schemas (UserCreate, UserResponse, etc.)
│   └── ... (other entity schemas)
├── services/                  # Business logic layer (Service pattern)
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   └── ... (other entity services)
├── templates/                 # Jinja2 templates (used by the entity generator)
│   ├── models/
│   ├── schemas/
│   ├── ...
├── tests/                     # Automated tests
│   ├── __init__.py
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
├── utils/                     # Utility scripts and helper functions
│   ├── __init__.py
│   ├── entity_generator.py    # The entity generator script
│   └── ... (other utilities)
├── .env.example               # Example environment variables file
├── .gitignore                 # Specifies intentionally untracked files that Git should ignore
├── alembic.ini                # Configuration file for Alembic
├── Dockerfile                 # Instructions to build a Docker image for the application
├── docker-compose.yml         # (If present) Defines and runs multi-container Docker applications
├── main.py                    # Main application entry point (FastAPI app instance)
├── mkdocs.yml                 # Configuration for the documentation site
├── requirements.txt           # Python package dependencies
└── readme.md / introduction.md # Project overview (now part of docs/)
```

## Key Directories Explained

-   **`alembic/`**: Manages database schema migrations using Alembic. When you change a SQLAlchemy model, you'll use Alembic to generate and apply migration scripts to update the database structure.
-   **`core/`**: Contains the fundamental building blocks of the application. This includes configuration loading (`config.py`), database connection setup (`database.py`), authentication and authorization logic (`auth.py`, `security.py`), and custom exceptions (`exceptions.py`).
-   **`docs/`**: Houses all project documentation, including what you are reading now. Generated using MkDocs.
-   **`models/`**: Defines the data structure of the application using SQLAlchemy ORM models. Each file typically represents a database table. The `base.py` often contains a declarative base or common columns like `id`, `created_at`, etc.
-   **`repositories/`**: Implements the Repository pattern. These classes encapsulate the logic for querying and manipulating data in the database, abstracting the database operations from the service layer. Typically, there's one repository per model.
-   **`routers/`**: Contains FastAPI `APIRouter` instances. Each router groups related API endpoints (e.g., all endpoints for managing users would be in `routers/user.py`). These are then included in the main FastAPI application in `main.py`.
-   **`schemas/`**: Holds Pydantic models used for data validation of incoming requests, serialization of outgoing responses, and defining data shapes.
-   **`services/`**: Contains the business logic of the application. Services orchestrate operations, often using one or more repositories to interact with data and performing tasks that are more complex than simple CRUD operations.
-   **`templates/`**: This directory specifically holds Jinja2 templates for the **Entity Generator** utility, not for serving HTML pages from the web application (unless the project also has such a feature, which would typically be in a separate `templates` directory or organized differently).
-   **`tests/`**: Contains all automated tests. It's usually split into `unit/` for testing individual components in isolation and `integration/` for testing interactions between components.
-   **`utils/`**: A place for miscellaneous utility scripts, helper functions, or tools like the `entity_generator.py` that assist in development but are not part of the core application runtime logic.

## Key Root Files

-   **`.env.example`**: An example template for the `.env` file, which is used to store environment-specific configurations (like database credentials, secret keys). The actual `.env` file is usually gitignored.
-   **`alembic.ini`**: Configuration for Alembic database migrations.
-   **`Dockerfile`**: Defines the steps to build a Docker image for the application, making it portable and easy to deploy.
-   **`docker-compose.yml`**: (If present) Used to define and manage multi-container Docker applications, often used in development to spin up the application along with its database and other services.
-   **`main.py`**: The entry point for the FastAPI application. It creates the main `FastAPI` instance and includes the API routers.
-   **`mkdocs.yml`**: Configuration file for the MkDocs documentation site.
-   **`requirements.txt`**: Lists all Python dependencies required by the project.

Understanding this structure is key to navigating the codebase and contributing effectively.
