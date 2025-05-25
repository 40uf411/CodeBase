from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import require_privileges
from cache.system import cache_response
from services.privilege_service import PrivilegeService
from schemas.privilege import PrivilegeResponse, PrivilegeCreate, PrivilegeUpdate

router = APIRouter(
    prefix="/privileges",
    tags=["privileges"],
    dependencies=[ require_privileges("privilege:read") ],  # no extra Depends()
)

@router.post(
    "/",
    response_model=PrivilegeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ require_privileges("privilege:create") ],
    summary="Create a new privilege"
)
async def create_privilege(
    privilege_in: PrivilegeCreate,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).create_privilege(privilege_in)

@router.get(
    "/",
    response_model=List[PrivilegeResponse],
    summary="List privileges"
)
@cache_response(ttl=3600)
async def list_privileges(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).get_privileges(skip=skip, limit=limit)

@router.get(
    "/entity/{entity}",
    response_model=List[PrivilegeResponse],
    summary="List privileges by entity"
)
@cache_response(ttl=3600)
async def list_privileges_by_entity(
    entity: str,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).get_privileges_by_entity(entity)

@router.post(
    "/entity/{entity}/crud",
    response_model=List[PrivilegeResponse],
    dependencies=[ require_privileges("privilege:create") ],
    summary="Generate CRUD privileges for an entity"
)
async def create_crud_privileges(
    entity: str,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).create_crud_privileges(entity)

@router.get(
    "/{privilege_id}",
    response_model=PrivilegeResponse,
    summary="Get a single privilege"
)
@cache_response(ttl=3600)
async def get_privilege(
    privilege_id: UUID,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).get_privilege(privilege_id)

@router.put(
    "/{privilege_id}",
    response_model=PrivilegeResponse,
    dependencies=[ require_privileges("privilege:update") ],
    summary="Update a privilege"
)
async def update_privilege(
    privilege_id: UUID,
    privilege_in: PrivilegeUpdate,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).update_privilege(privilege_id, privilege_in)

@router.delete(
    "/{privilege_id}",
    response_model=PrivilegeResponse,
    dependencies=[ require_privileges("privilege:delete") ],
    summary="Delete a privilege"
)
async def delete_privilege(
    privilege_id: UUID,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).delete_privilege(privilege_id)

@router.post(
    "/{privilege_id}/assign-to-role/{role_id}",
    response_model=PrivilegeResponse,
    dependencies=[
        require_privileges("privilege:update"),
        require_privileges("role:update"),
    ],
    summary="Assign a privilege to a role"
)
async def assign_privilege_to_role(
    privilege_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).assign_privilege_to_role(privilege_id, role_id)

@router.delete(
    "/{privilege_id}/remove-from-role/{role_id}",
    response_model=PrivilegeResponse,
    dependencies=[
        require_privileges("privilege:update"),
        require_privileges("role:update"),
    ],
    summary="Remove a privilege from a role"
)
async def remove_privilege_from_role(
    privilege_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
):
    return PrivilegeService(db).remove_privilege_from_role(privilege_id, role_id)