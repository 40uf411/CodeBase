# Installation Guide

This guide will walk you through setting up your development environment for My Platform.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python**: Version 3.8 or higher is recommended. You can download it from [python.org](https://www.python.org/).
- **pip**: Python's package installer. It usually comes with Python. Ensure it's upgraded:
  ```bash
  python -m pip install --upgrade pip
  ```
- **Git**: For cloning the repository. You can download it from [git-scm.com](https://git-scm.com/).
- **Docker and Docker Compose (Optional but Recommended)**: If you plan to use Docker for running the database or other services.

## 1. Clone the Repository

First, clone the project repository from your version control system (e.g., GitHub, GitLab):

```bash
git clone <your-repository-url>
cd <repository-directory-name>
```
Replace `<your-repository-url>` and `<repository-directory-name>` with the actual URL and the directory name.

## 2. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with global Python packages.

**Create a virtual environment:**

```bash
python -m venv venv
```
This creates a `venv` directory in your project folder.

**Activate the virtual environment:**

-   **On macOS and Linux:**
    ```bash
    source venv/bin/activate
    ```
-   **On Windows:**
    ```bash
    .\venv\Scripts\activate
    ```
You should see `(venv)` at the beginning of your command prompt, indicating the virtual environment is active.

## 3. Install Dependencies

All required Python packages are listed in the `requirements.txt` file. Install them using pip:

```bash
pip install -r requirements.txt
```
This will install the application dependencies as well as the documentation tools (`mkdocs`, `mkdocs-material`, etc.).

The contents of `requirements.txt` include:
```
fastapi
uvicorn
sqlalchemy>=1.4
asyncpg
pydantic
alembic
psycopg2-binary
python-jose
passlib
python-multipart
redis
requests
rich
inquirer
mkdocs
mkdocs-material
```

## 4. Environment Configuration

The application might require certain environment variables to be set (e.g., database connection strings, API keys, secret keys).

- Create a `.env` file in the project root by copying the example template if provided (e.g., `.env.example`).
  ```bash
  cp .env.example .env  # If .env.example exists
  ```
- Edit the `.env` file and fill in the necessary configuration values.

Refer to the configuration section or `core/config.py` for details on required environment variables.

## 5. Database Setup

If the application requires a database, ensure it's set up and accessible.

- **Using Docker (Recommended for Development):** If a `docker-compose.yml` file is provided, you can typically start the database service (e.g., PostgreSQL) with:
  ```bash
  docker-compose up -d db_service_name # Replace db_service_name with the actual service name
  ```
- **Manual Setup:** If you're managing the database manually, ensure the database server is running and the necessary database/user are created.

**Run Database Migrations:**
Once the database is accessible and configured in your `.env` file, apply the database migrations using Alembic:
```bash
alembic upgrade head
```
This will create all the necessary tables in your database.

## 6. Initial Application Setup (If Any)

Some applications might require an initial setup step, such as creating a superuser or bootstrapping initial data. Refer to specific application instructions if available. For example, to create an initial superuser, there might be a script or a command:

```bash
# Example: python initial_setup.py --create-superuser
```
(Check the project's README or specific setup scripts for such commands.)

## Next Steps

Once you've completed these steps, you should be ready to run the application. Proceed to the "Running the Application" guide.

To work on documentation:
- Start the live preview server: `mkdocs serve`
- Build the static site: `mkdocs build`
