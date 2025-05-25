from typing import Optional, List
from pydantic import EmailStr, Field, BaseModel, EmailStr
from uuid import UUID

from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
from .oauth_account import OAuthAccountResponse

class UserBase(BaseSchema):
    """
    Base schema for User model.
    """
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    # is_streamable: Optional[bool] = False


class UserCreate(BaseCreateSchema):
    """
    Schema for creating a new user.
    """
    email: EmailStr
    password: str
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    # is_streamable: Optional[bool] = False


class UserCreateOAuth(BaseCreateSchema):
    """
    Schema for creating a new user via OAuth.
    """
    email: EmailStr
    full_name: Optional[str] = None
    oauth_provider: str
    oauth_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None


class UserUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing user.
    """
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    full_name: Optional[str] = None
    # is_streamable: Optional[bool] = None


class UserResponse(BaseResponseSchema):
    """
    Schema for user response.
    """
    email: EmailStr
    is_active: bool
    is_superuser: bool
    full_name: Optional[str]
    # is_streamable: Optional[bool]
    has_password: bool


class UserDetailResponse(UserResponse):
    """
    Schema for detailed user response with OAuth accounts.
    """
    oauth_accounts: List[OAuthAccountResponse] = []


class Token(BaseSchema):
    """
    Schema for authentication tokens.
    """
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class TokenPayload(BaseSchema):
    """
    Schema for token payload.
    """
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class BootstrapAdminRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    full_name: Optional[str] = None


class BootstrapAdminResponse(BaseModel):
    email: EmailStr
    password: str