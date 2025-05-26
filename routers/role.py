from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from sqlalchemy.orm import Session

# from core.database import get_db # Replaced by repository/service dependencies
from core.auth import require_privileges
from cache.system import cache_response
from repositories.role_repository import RoleRepository, get_role_repository # Added get_role_repository
from services.privilege_service import PrivilegeService, get_privilege_service # Added get_privilege_service
from schemas.role import RoleResponse, RoleCreate, RoleUpdate, RoleWithPrivileges

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[require_privileges("role:read")]
)

@router.get("/", response_model=List[RoleResponse], summary="List roles")
@cache_response(ttl=6 * 3600)
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role_repo: RoleRepository = Depends(get_role_repository) # Changed
) -> List[RoleResponse]:
    """
    Retrieve a list of roles. Requires 'role:read' privilege.
    """
    return role_repo.get_all(skip=skip, limit=limit) # Changed

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[require_privileges("role:create")],
             summary="Create a new role")
async def create_role(
    role_in: RoleCreate,
    role_repo: RoleRepository = Depends(get_role_repository), # Changed
    priv_service: PrivilegeService = Depends(get_privilege_service) # Added
) -> RoleResponse:
    """
    Create a new role. Requires 'role:create' privilege.
    """
    # Bootstrap CRUD privileges for 'role'
    priv_service.create_crud_privileges("role") # Changed
    return role_repo.create(role_in.dict()) # Changed

@router.get("/{role_id}", response_model=RoleWithPrivileges, summary="Get a role by ID")
@cache_response(ttl=3600)
async def get_role(
    role_id: UUID = Path(..., title="Role ID"),
    role_repo: RoleRepository = Depends(get_role_repository) # Changed
) -> RoleWithPrivileges:
    """
    Get a specific role and its privileges. Requires 'role:read' privilege.
    """
    role = role_repo.get(role_id) # Changed
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    names = [p.name for p in role.privileges]
    return RoleWithPrivileges(**role.__dict__, privileges=names)

@router.put("/{role_id}", response_model=RoleResponse,
            dependencies=[require_privileges("role:update")],
            summary="Update a role")
async def update_role(
    role_in: RoleUpdate,
    role_id: UUID = Path(..., title="Role ID"),
    role_repo: RoleRepository = Depends(get_role_repository) # Changed
) -> RoleResponse:
    """
    Update an existing role. Requires 'role:update' privilege.
    """
    # Assuming RoleRepository.update now returns Optional[Role] and service layer handles 404
    # For now, directly calling repo.update as per existing structure, which raises HTTP 404 if not found
    # This part might need further adjustment if RoleService is created or if repo.update changes.
    # Based on current BaseRepository, repo.update returns the object or raises 404.
    # If repo.update was changed to return Optional[T] and not raise 404 (as per previous subtask),
    # then this router would need to handle the None case.
    # The `repositories/base_repository.py` `update` was changed to return `Optional[T]`
    # and return `None` if not found. So this router needs to handle it.
    updated_role = role_repo.update(role_id, role_in.dict(exclude_unset=True))
    if not updated_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found for update.")
    return updated_role


@router.delete("/{role_id}", response_model=RoleResponse,
               dependencies=[require_privileges("role:delete")],
               summary="Delete a role")
async def delete_role(
    role_id: UUID = Path(..., title="Role ID"),
    hard_delete: bool = Query(False, description="Permanently delete if true"),
    role_repo: RoleRepository = Depends(get_role_repository) # Changed
) -> RoleResponse:
    """
    Delete (soft or hard) a role. Requires 'role:delete' privilege.
    """
    # Similar to update, if repo.delete returns Optional[T]
    deleted_role = role_repo.delete(role_id, hard_delete=hard_delete)
    if not deleted_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found for deletion.")
    return deleted_role
