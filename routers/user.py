from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Path, Query, Response, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import require_privileges
from cache.system import cache_response
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.privilege_service import PrivilegeService
from schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[require_privileges("user:read")]
)

@router.get("/", response_model=List[UserResponse], summary="List users")
@cache_response(ttl=6 * 3600)  # Cache for 6 hours
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Retrieve a list of users. Requires 'user:read' privilege.
    """
    repo = UserRepository(db)
    users = repo.get_all(skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[require_privileges("user:create")],
             summary="Create a new user")
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Create a new user. Requires 'user:create' privilege.
    """
    # Bootstrap CRUD privileges for 'user'
    PrivilegeService(db).create_crud_privileges("user")
    # Delegate to AuthService for hashing & creation
    return AuthService(db).create_user(user_in)

@router.get("/{user_id}", response_model=UserResponse, summary="Get a user by ID")
@cache_response(ttl=3600)  # Cache for 1 hour
async def get_user(
    user_id: UUID = Path(..., title="User ID"),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get a specific user by ID. Requires 'user:read' privilege.
    """
    user = UserRepository(db).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse,
            dependencies=[require_privileges("user:update")],
            summary="Update a user")
async def update_user(
    user_in: UserUpdate,
    user_id: UUID = Path(..., title="User ID"),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update an existing user. Requires 'user:update' privilege.
    """
    updated = AuthService(db).update_user(user_id, user_in.dict(exclude_unset=True))
    return updated

@router.delete("/{user_id}", response_model=UserResponse,
               dependencies=[require_privileges("user:delete")],
               summary="Delete a user")
async def delete_user(
    user_id: UUID = Path(..., title="User ID"),
    hard_delete: bool = Query(False, description="Permanently delete if true"),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Delete (soft or hard) a user. Requires 'user:delete' privilege.
    """
    repo = UserRepository(db)
    user = repo.delete(user_id, hard_delete=hard_delete)
    return user
