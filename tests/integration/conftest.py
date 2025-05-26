import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
import io
import logging


# Adjust import paths based on your project structure
# Assuming 'main.py' and 'core.database' are discoverable
from main import app # Your FastAPI app
from core.database import Base, get_db, SessionLocal # Assuming get_db and SessionLocal
from services.activity_logger_service import JsonFormatter # For log capture helper

# --- Database Setup for Tests ---
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_integration.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_database_tables():
    # Create tables at the beginning of the test session
    if "sqlite" in SQLALCHEMY_DATABASE_URL: # Only remove if it's a file-based DB
        if os.path.exists("./test_integration.db"):
            os.remove("./test_integration.db")
    Base.metadata.create_all(bind=engine)
    yield # Test session runs
    # Optional: Drop tables or clean up after test session
    # Base.metadata.drop_all(bind=engine) # Or keep for inspection
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        if os.path.exists("./test_integration.db"):
            os.remove("./test_integration.db")


@pytest.fixture(scope="function")
def db() -> Generator[SessionLocal, None, None]:
    """
    Fixture to provide a database session for each test function.
    Rolls back transactions to ensure test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: SessionLocal) -> Generator[TestClient, None, None]:
    """
    Fixture to provide a TestClient instance with an overridden db dependency.
    """
    def override_get_db():
        try:
            yield db
        finally:
            db.close() # Should be handled by db fixture's rollback/close

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    del app.dependency_overrides[get_db] # Clean up override


# --- Log Capture Helper ---
@pytest.fixture(scope="function")
def log_capture():
    logger = logging.getLogger("activity_logger") # Target the specific logger
    log_stream = io.StringIO()
    
    # Use the same JsonFormatter as the application
    formatter = JsonFormatter() 
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(formatter)
    
    original_handlers = logger.handlers[:]
    original_level = logger.level
    
    # Clear existing handlers for the test to ensure only our stream_handler is active
    # and prevent duplicate logging if tests run in parallel or affect global logger state.
    logger.handlers = [] 
    logger.addHandler(stream_handler)
    # Ensure logs at INFO level (or whatever your app uses) are captured
    logger.setLevel(logging.INFO) 
    
    yield log_stream # The stream where logs are captured
    
    # Restore original logger state
    log_stream.close()
    logger.handlers = original_handlers
    logger.level = original_level
    # Important: Also clear the singleton's config if it was loaded,
    # to avoid state leakage between tests if ActivityLoggerService is a singleton
    # This might require a reset method on the service or careful test structure.
    from services.activity_logger_service import ActivityLoggerService
    if ActivityLoggerService._instance:
        ActivityLoggerService._instance._initialized_db_config = False
        ActivityLoggerService._instance.config = {} # Reset its config


# --- Authentication Helpers (Placeholders - Implement based on your actual auth system) ---
# These would typically involve creating users in the DB and then logging them in via API.

@pytest.fixture(scope="function")
def admin_user_headers(client: TestClient, db: SessionLocal) -> dict:
    # This is a placeholder. In a real scenario:
    # 1. Create an admin user in the db.
    #    - Need User model, AuthService/UserRepository.
    #    - Ensure this user has the 'admin:logging_settings:manage' privilege.
    #      This might involve creating the privilege and role, then assigning.
    # 2. Login as this admin user via the /auth/login endpoint.
    # 3. Return the authorization headers.
    
    # For PoC, we might need to bypass auth or use a known superuser if one exists by default.
    # If your app has a bootstrap mechanism for a superuser:
    # from core.config import settings
    # login_data = {"username": settings.FIRST_SUPERUSER, "password": settings.FIRST_SUPERUSER_PASSWORD}
    # response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    # if response.status_code == 200:
    #     tokens = response.json()
    #     return {"Authorization": f"Bearer {tokens['access_token']}"}
    # else: # Fallback if no default superuser or login fails for this PoC
    #     print(f"WARN: Admin login failed for tests: {response.status_code} {response.text}")
    #     # This indicates a problem with test setup or prerequisite of a superuser.
    #     # For now, returning an empty dict, which will cause auth tests to fail as expected if auth is enforced.
    #     # In a real test suite, this fixture *must* provide valid admin headers.
    #     pytest.skip("Admin user login for tests not fully implemented or failed. Skipping auth-dependent tests.")
    #     return {}

    # Simplified version for now: assume a bypass or pre-existing admin for tests that need it.
    # Replace with actual admin user creation and login.
    # For now, we'll rely on tests either mocking auth or being run where auth isn't strictly blocking for this PoC.
    # This part is CRITICAL for real auth testing.
    # If a simple "is_superuser" flag is used and can be set:
    from models.user import User
    from core.security import get_password_hash, create_access_token
    from datetime import timedelta

    admin_email = "admin_integration_test@example.com"
    admin_password = "testadminpassword"
    
    user = db.query(User).filter(User.email == admin_email).first()
    if not user:
        user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name="Admin Test User",
            is_active=True,
            is_superuser=True # Crucial for bypassing privilege checks in some setups
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Manually create a token for this user (simulates login)
    # This bypasses the /auth/login endpoint for simplicity in this fixture.
    # In a full integration test, you'd call client.post("/auth/login").
    access_token = create_access_token(
        subject=str(user.id), expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def regular_user_headers(client: TestClient, db: SessionLocal) -> dict:
    # Placeholder: Create a non-admin user and login.
    from models.user import User
    from core.security import get_password_hash, create_access_token
    from datetime import timedelta

    user_email = "user_integration_test@example.com"
    user_password = "testuserpassword"

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        user = User(
            email=user_email,
            hashed_password=get_password_hash(user_password),
            full_name="Regular Test User",
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(
        subject=str(user.id), expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

# Ensure the file ends with a newline.
