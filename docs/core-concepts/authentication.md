# Authentication

Authentication is the process of verifying the identity of a user, system, or application attempting to access resources. In My Platform, authentication is primarily handled using a token-based system, typically with JSON Web Tokens (JWT).

## Token-Based Authentication (JWT)

Instead of using traditional sessions, our platform employs JWTs for authenticating API requests. When a user successfully logs in, they are issued an **access token** and potentially a **refresh token**.

### Access Tokens

-   **Purpose**: An access token is a short-lived credential that grants access to protected resources (API endpoints).
-   **Usage**: The client application must include the access token in the `Authorization` header of HTTP requests to protected endpoints, using the `Bearer` scheme.
    ```http
    Authorization: Bearer <your_access_token>
    ```
-   **Lifespan**: Access tokens are intentionally short-lived (e.g., 15 minutes to a few hours) to minimize the risk if a token is compromised.
-   **Content**: JWTs are self-contained and typically include a payload (`claims`) with user identification (e.g., user ID, email) and token expiration time (`exp`). They are digitally signed by the server to ensure their integrity.

### Refresh Tokens (If Implemented)

-   **Purpose**: A refresh token is a longer-lived credential used to obtain a new access token when the current access token expires. This allows users to remain logged in for extended periods without repeatedly entering their credentials.
-   **Usage**: When an access token expires, the client can send the refresh token to a specific token refresh endpoint (e.g., `/auth/refresh-token`) to get a new access token.
-   **Lifespan**: Refresh tokens have a much longer lifespan (e.g., days or weeks) than access tokens.
-   **Security**: Refresh tokens must be stored securely by the client. They are often HttpOnly cookies or stored in secure storage if it's a mobile/SPA client. If a refresh token is compromised, an attacker could potentially generate new access tokens. Mechanisms like refresh token rotation can enhance security.

## Password Management

User passwords are never stored in plaintext. We use strong hashing algorithms to protect user credentials.

-   **Hashing Algorithm**: Typically, a library like `passlib` is used, configured with a strong algorithm such as bcrypt or Argon2.
-   **Storage**: The hashed password for each user is stored in the `hashed_password` column of the `user` table in the database.
-   **Verification**: During login, the password provided by the user is hashed using the same algorithm and then compared against the stored hash.

## Core Authentication Modules & Files

The primary logic for authentication is centralized in the following areas:

-   **`core/auth.py`**:
    -   Functions for creating and decoding JWT access (and refresh) tokens.
    -   Utility functions for password hashing and verification (often wrappers around `passlib`).
    -   FastAPI dependency injectors (e.g., `get_current_user`, `require_privileges`) used to protect API endpoints and retrieve authenticated user information.
-   **`core/security.py`**:
    -   May define the `passlib` hashing context (`CryptContext`).
    -   Contains security-related constants, such as token expiration times and the secret key used for signing JWTs (though the actual secret key value should come from environment variables via `core/config.py`).
-   **`routers/auth.py`**:
    -   Defines API endpoints related to authentication, such as:
        -   Login (e.g., `/auth/token`, `/auth/login`): Takes user credentials, verifies them, and returns access/refresh tokens.
        -   Refresh Token (e.g., `/auth/refresh-token`): Accepts a refresh token and issues a new access token.
        -   (Potentially) Endpoints for password recovery, password reset, and user registration if not handled elsewhere.
-   **`models/user.py`**:
    -   The `User` SQLAlchemy model, which includes the `email` and `hashed_password` fields crucial for authentication.
-   **`schemas/user.py` (and `schemas/auth.py` if it exists)**:
    -   Pydantic schemas for authentication-related data, such as:
        -   Login request (username/password).
        -   Token response (access_token, refresh_token, token_type).
        -   Token payload (data encoded within the JWT).

## Login Flow (Simplified)

1.  The user provides their credentials (e.g., email and password) via a login form or API request.
2.  The request is sent to the login endpoint (e.g., `/auth/token`) in `routers/auth.py`.
3.  The `AuthService` (or logic within the router) retrieves the user by email from the database using `UserRepository`.
4.  If the user exists, the provided password is
    hashed and compared with the `hashed_password` stored for that user (using utilities from `core/auth.py` or `core/security.py`).
5.  If the password matches, the system generates a new JWT access token (and possibly a refresh token). The access token contains user identifiers (like user ID or email) and an expiration claim.
6.  The tokens are returned to the client.
7.  The client stores these tokens securely and uses the access token in the `Authorization` header for subsequent requests to protected API endpoints.

## Protecting Endpoints

API endpoints are protected using FastAPI's dependency injection system. Functions defined in `core/auth.py` (like `get_current_active_user` or a more generic `require_privileges`) are used as dependencies for routes that require authentication.

**Example:**
```python
from fastapi import APIRouter, Depends
from ..core.auth import get_current_active_user # Or your specific dependency
from ..schemas.user import UserResponse

router = APIRouter()

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    # If the request reaches here, the user is authenticated.
    # 'current_user' will contain the authenticated user's data.
    return current_user
```
If a valid token is not provided or if the token is expired, the dependency will raise an `HTTPException` (typically a 401 Unauthorized), preventing the route handler from executing.

This token-based authentication mechanism provides a stateless and secure way to manage user sessions in a modern web application.
