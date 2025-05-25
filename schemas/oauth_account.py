from typing import Optional, List
from pydantic import EmailStr, Field
from uuid import UUID

from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class OAuthAccountBase(BaseSchema):
    """
    Base schema for OAuthAccount model.
    """
    provider: str
    provider_user_id: str
    access_token: Optional[str] = None
    expires_at: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuthAccountCreate(BaseCreateSchema):
    """
    Schema for creating a new OAuth account.
    """
    provider: str
    provider_user_id: str
    access_token: Optional[str] = None
    expires_at: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: UUID


class OAuthAccountUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing OAuth account.
    """
    access_token: Optional[str] = None
    expires_at: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuthAccountResponse(BaseResponseSchema):
    """
    Schema for OAuth account response.
    """
    provider: str
    provider_user_id: str
    user_id: UUID
