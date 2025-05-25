from typing import Optional, List
from pydantic import Field

from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class RoleBase(BaseSchema):
    """
    Base schema for Role model.
    """
    name: str
    description: Optional[str] = None
    # is_streamable: Optional[bool] = False


class RoleCreate(BaseCreateSchema):
    """
    Schema for creating a new role.
    """
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class RoleUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing role.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    # is_streamable: Optional[bool] = None


class RoleResponse(BaseResponseSchema):
    """
    Schema for role response.
    """
    name: str
    description: Optional[str]


class RoleWithPrivileges(RoleResponse):
    """
    Schema for role response with privileges.
    """
    privileges: List[str] = []
