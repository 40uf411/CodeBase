from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import require_privileges
from cache.system import cache_response
from repositories.role_repository import RoleRepository
from services.privilege_service import PrivilegeService
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
    db: Session = Depends(get_db)
) -> List[RoleResponse]:
    """
    Retrieve a list of roles. Requires 'role:read' privilege.
    """
    return RoleRepository(db).get_all(skip=skip, limit=limit)

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[require_privileges("role:create")],
             summary="Create a new role")
async def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db)
) -> RoleResponse:
    """
    Create a new role. Requires 'role:create' privilege.
    """
    # Bootstrap CRUD privileges for 'role'
    PrivilegeService(db).create_crud_privileges("role")
    return RoleRepository(db).create(role_in.dict())

@router.get("/{role_id}", response_model=RoleWithPrivileges, summary="Get a role by ID")
@cache_response(ttl=3600)
async def get_role(
    role_id: UUID = Path(..., title="Role ID"),
    db: Session = Depends(get_db)
) -> RoleWithPrivileges:
    """
    Get a specific role and its privileges. Requires 'role:read' privilege.
    """
    role = RoleRepository(db).get(role_id)
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
    db: Session = Depends(get_db)
) -> RoleResponse:
    """
    Update an existing role. Requires 'role:update' privilege.
    """
    return RoleRepository(db).update(role_id, role_in.dict(exclude_unset=True))

@router.delete("/{role_id}", response_model=RoleResponse,
               dependencies=[require_privileges("role:delete")],
               summary="Delete a role")
async def delete_role(
    role_id: UUID = Path(..., title="Role ID"),
    hard_delete: bool = Query(False, description="Permanently delete if true"),
    db: Session = Depends(get_db)
) -> RoleResponse:
    """
    Delete (soft or hard) a role. Requires 'role:delete' privilege.
    """
    return RoleRepository(db).delete(role_id, hard_delete=hard_delete)
