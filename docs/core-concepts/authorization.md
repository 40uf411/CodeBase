# Authorization (Role-Based Access Control - RBAC)

Authorization is the process of determining whether an authenticated user has the necessary permissions to perform a specific action or access a particular resource. My Platform employs a Role-Based Access Control (RBAC) system.

## Overview

Once a user is authenticated (their identity is verified), RBAC determines what they are allowed to do. This is achieved by assigning users to **roles**, and then granting **privileges** (permissions) to those roles.

## Core Concepts

### 1. Privileges

-   **Definition**: A privilege is a granular permission that represents the ability to perform a specific action on a particular entity or resource.
-   **Structure**: Each privilege typically has:
    -   `name`: A unique identifier for the privilege, often following a pattern like `entity:action` (e.g., `user:create`, `product:read`, `article:update_own`).
    -   `description`: A human-readable description of what the privilege allows.
    -   `entity`: The name of the entity this privilege pertains to (e.g., "user", "product").
    -   `action`: The type of action allowed (e.g., "create", "read", "update", "delete", "read_own", "update_all").
-   **Examples**:
    -   `user:read`: Allows reading user information.
    -   `product:create`: Allows creating new products.
    -   `order:delete_all`: Allows deleting any order (typically an admin privilege).

### 2. Roles

-   **Definition**: A role is a named collection of privileges. Instead of assigning individual privileges directly to users, users are assigned one or more roles.
-   **Purpose**: Roles simplify permission management. If a set of permissions needs to change, you modify the role, and all users assigned to that role automatically inherit the changes.
-   **Examples**:
    -   `viewer`: Might have read-only privileges for several entities.
    -   `editor`: Might have read and update privileges for specific content types.
    -   `admin`: Might have all privileges across all entities.

## Models Involved

The RBAC system relies on the following SQLAlchemy models:

-   **`models/privilege.py` (`Privilege` model)**:
    -   Stores the definition of each available privilege (name, description, entity, action).
-   **`models/role.py` (`Role` model)**:
    -   Stores the definition of roles (e.g., role name like "admin", "editor").
    -   Has a many-to-many relationship with the `Privilege` model via the `role_privileges` association table. This links roles to the specific privileges they grant.
-   **`models/user.py` (`User` model)**:
    -   Represents users of the system.
    -   Has a many-to-many relationship with the `Role` model via the `user_roles` association table. This assigns roles to users.

## How Authorization Works

1.  **Authentication**: The user first authenticates (e.g., via JWT) to prove their identity. The system retrieves the authenticated user object, which includes their assigned roles.
2.  **Privilege Check**: When an authenticated user attempts to access a protected API endpoint or perform an action:
    a.  The endpoint is typically decorated with a dependency (e.g., `require_privileges`) that specifies the privilege(s) needed for that operation.
    b.  The `require_privileges` function (usually found in `core/auth.py`) inspects the user's roles.
    c.  For each role assigned to the user, it checks the privileges associated with that role.
    d.  If any of the user's roles contain the required privilege(s), access is granted.
    e.  If the required privilege(s) are not found among the user's roles, access is denied, typically by raising an `HTTPException` (e.g., 403 Forbidden).

## Defining and Managing Privileges & Roles

-   **Creating Privileges**:
    -   Privileges are often pre-defined or seeded into the `privilege` table when the application is set up or a new module/entity is added.
    -   The Entity Generator tool, for instance, creates a `generated_privileges.sql` script with basic CRUD privileges (`entity:create`, `entity:read`, `entity:update`, `entity:delete`) for each new entity. These need to be manually run against the database.
    -   An administrative interface might also allow for dynamic creation/management of privileges.
-   **Creating Roles and Assigning Privileges**:
    -   Roles (like "Administrator", "ContentEditor", "BasicUser") are typically created in the `role` table.
    -   Privileges are then associated with these roles via the `role_privileges` table. This is often done through an admin panel or seed scripts.
-   **Assigning Roles to Users**:
    -   Users are assigned roles via the `user_roles` table. This assignment dictates the set of effective privileges a user possesses. This can be done during user creation, through an admin interface, or by specific application logic.

## Protecting Endpoints with `require_privileges`

The `core/auth.py` module usually provides a FastAPI dependency for checking privileges.

**Example Usage in a Router:**
```python
from fastapi import APIRouter, Depends
from ..core.auth import require_privileges

router = APIRouter()

@router.post("/products", dependencies=[Depends(require_privileges("product:create"))])
async def create_product(product_data: dict):
    # Logic to create a product
    return {"message": "Product created successfully"}

@router.get("/products/{product_id}", dependencies=[Depends(require_privileges("product:read"))])
async def get_product(product_id: str):
    # Logic to get a product
    return {"id": product_id, "name": "Sample Product"}

# To require multiple privileges (user must have ALL of them)
@router.put("/orders/{order_id}", dependencies=[Depends(require_privileges("order:update", "order:notify_customer"))])
async def update_order_and_notify(order_id: str, order_data: dict):
    # Logic here
    return {"message": "Order updated and customer notified"}

# It's also common to apply privilege checks to an entire router:
# admin_router = APIRouter(dependencies=[Depends(require_privileges("admin_access"))])
```
In this example, if a user tries to access `POST /products` but their roles do not grant the `product:create` privilege, they will receive a 403 Forbidden error.

## Superuser / Special Privileges

-   **Superuser Flag**: The `User` model often has an `is_superuser` boolean flag. If a user has this flag set to `true`, the `require_privileges` dependency might bypass the normal role/privilege checks and grant them access to all resources. This is a common pattern for administrative override.
-   **Wildcard Privileges**: While not explicitly detailed in the current models, some RBAC systems support wildcard privileges (e.g., `entity:*` or `*:admin`). This is not a standard feature here unless specifically implemented.

This RBAC system provides a flexible and robust way to manage user permissions across the platform.
