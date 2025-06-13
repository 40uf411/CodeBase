# Database

This document provides an overview of the database setup, Object-Relational Mapper (ORM), migration management, and data access patterns used in this project.

## Database System: PostgreSQL

The project utilizes **PostgreSQL**, a powerful, open-source object-relational database system known for its reliability, feature robustness, and performance. PostgreSQL offers advanced features like complex queries, foreign keys, triggers, JSONB support, and excellent concurrency control.

## Object-Relational Mapper (ORM): SQLAlchemy

We use **SQLAlchemy** as our ORM. SQLAlchemy is a comprehensive toolkit that provides a full suite of well-known enterprise-level persistence patterns, designed for efficient and high-performing database access.

### Benefits of Using an ORM (SQLAlchemy)

- **Productivity:** Allows developers to interact with the database using Python objects and methods, abstracting away much of the SQL boilerplate.
- **Database Agnostic (to an extent):** While we use PostgreSQL, SQLAlchemy can connect to various database backends, making it easier to switch if needed (though specific RDBMS features might not always be portable).
- **Improved Readability and Maintainability:** Python code is often easier to read and maintain than complex SQL queries embedded in application logic.
- **Security:** Helps prevent SQL injection vulnerabilities by using parameterized queries.
- **Automatic Schema Management:** Facilitates tasks like creating tables from model definitions.

### Defining Models

Database models (representing tables) are defined as Python classes inheriting from a declarative base provided by SQLAlchemy. These models are typically located in the `models/` directory. Each class attribute maps to a column in the database table.

*Example (conceptual):*
```python
# In a file like models/user.py
from sqlalchemy import Column, Integer, String
from core.database import Base # Assuming Base is defined in core.database

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
```
*For actual model definitions, please refer to the files within the `models/` directory.*

### Session Management (`core/database.py`)

SQLAlchemy interacts with the database through a **Session**. A session is a workspace for all the objects loaded or associated with it. It brokers all communications with the database and represents a "holding zone" for all objects which you’ve loaded or associated with it during its lifespan.

The setup for the database engine, session factory (`SessionLocal`), and the declarative base (`Base`) are typically configured in `core/database.py`. This file will contain the logic to create a database engine instance and provide a way to get a database session for each request or operation.

*Key components in `core/database.py` (conceptual):*
- Database URL configuration (see "Configuration Details" below).
- `create_engine()` to establish the database connection.
- `sessionmaker()` to create the `SessionLocal` class, which generates new Session objects.
- `declarative_base()` to create the `Base` class for model definitions.
- A dependency or utility function to get a DB session (e.g., `get_db`) for use in API endpoints or service layers.

### Basic CRUD Operations with SQLAlchemy

SQLAlchemy provides an intuitive way to perform Create, Read, Update, and Delete (CRUD) operations:

- **Create:**
  ```python
  db_user = models.User(username="newuser", email="newuser@example.com")
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  ```
- **Read:**
  ```python
  user = db.query(models.User).filter(models.User.username == "newuser").first()
  users = db.query(models.User).all()
  user_by_id = db.query(models.User).get(1) # Using .get() with primary key
  ```
- **Update:**
  ```python
  user_to_update = db.query(models.User).filter(models.User.username == "newuser").first()
  if user_to_update:
      user_to_update.email = "updated_email@example.com"
      db.commit()
      db.refresh(user_to_update)
  ```
- **Delete:**
  ```python
  user_to_delete = db.query(models.User).filter(models.User.username == "newuser").first()
  if user_to_delete:
      db.delete(user_to_delete)
      db.commit()
  ```

## Database Migrations: Alembic

Database schema migrations are managed using **Alembic**. Alembic is a lightweight database migration tool for SQLAlchemy. It allows for tracking and applying changes to the database schema over time as the application evolves.

### How to Generate New Migrations

After making changes to your SQLAlchemy models (e.g., adding a new table, adding a column to an existing table), you can generate a new migration script:
```bash
alembic revision -m "short_description_of_changes"
```
This command creates a new migration file in the `alembic/versions/` directory. You then need to edit this file to include the specific schema changes using Alembic's `op` directives (e.g., `op.create_table()`, `op.add_column()`). Alembic can sometimes autogenerate simple migrations based on model changes if configured to do so, but complex changes often require manual scripting.

### How to Apply Migrations

To apply all pending migrations to the database, bringing it to the latest version:
```bash
alembic upgrade head
```

### How to Downgrade Migrations

To revert a migration, you can downgrade to a specific version or step back one version:
```bash
# Downgrade to a specific version
alembic downgrade <version_number>

# Downgrade by one revision
alembic downgrade -1
```
Each migration script should implement both `upgrade()` and `downgrade()` functions to ensure changes can be safely applied and reverted.

## Connection Pooling

Database connection pooling is crucial for performance and stability in web applications. Opening and closing database connections for every request is resource-intensive. A connection pool maintains a set of open database connections that can be reused by the application.

SQLAlchemy's Engine typically manages a connection pool by default (e.g., `QueuePool`). This significantly reduces the overhead of establishing connections and improves response times. Configuration of the pool (e.g., pool size, overflow) can be done during engine creation if defaults are not suitable.

## Configuration Details

Database connection parameters are configured primarily through environment variables. The main variable is typically `DATABASE_URL`, which specifies the database dialect, user, password, host, port, and database name.

*Example `DATABASE_URL` for PostgreSQL:*
```
DATABASE_URL="postgresql://user:password@host:port/dbname"
```
This URL is then used in `core/database.py` when creating the SQLAlchemy engine:
```python
# In core/database.py
from sqlalchemy import create_engine
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL) # Pool arguments can be added here if needed
```
Ensure that appropriate environment variables are set in your development, staging, and production environments.

## Repository Pattern (`repositories/`)

To further abstract database interactions and promote separation of concerns, this project employs the **Repository pattern**. Repositories provide a cleaner API for data access and centralize data access logic. Instead of scattering SQLAlchemy queries throughout the application (e.g., in API route handlers or business logic services), these operations are encapsulated within repository classes.

Each repository is typically responsible for a specific model or a group of related models. For example, `UserRepository` would handle all database operations related to `User` models.

*Conceptual structure:*
- `repositories/base_repository.py`: Might define a base repository class with common CRUD methods.
- `repositories/user_repository.py`: Inherits from the base and implements user-specific data access methods.

This pattern makes the codebase more testable (repositories can be mocked) and easier to maintain.

## Database Design Choices and Conventions

*(This section should be filled with project-specific information. Examples include:)*
- **Naming Conventions:** e.g., tables are plural, columns are snake_case.
- **Use of UUIDs:** If primary keys are UUIDs instead of auto-incrementing integers.
- **Soft Deletes:** If records are marked as deleted instead of being physically removed.
- **Audit Trails:** If changes to important tables are logged.
- **Specific Indexing Strategies:** Any non-obvious indexing choices made for performance.
- **Use of Schemas (PostgreSQL Schemas):** If the database is organized into multiple schemas.

Please consult the project's lead developers or existing database schema for detailed conventions.
