from typing import Optional, List
from pydantic import Field

from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class PrivilegeBase(BaseSchema):
    """
    Base schema for Privilege model.
    """
    name: str
    description: Optional[str] = None
    # is_streamable: Optional[bool] = False


class PrivilegeCreate(BaseCreateSchema):
    """
    Schema for creating a new privilege.
    """
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class PrivilegeUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing privilege.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    # is_streamable: Optional[bool] = None


class PrivilegeResponse(BaseResponseSchema):
    """
    Schema for privilege response.
    """
    name: str
    description: Optional[str]
