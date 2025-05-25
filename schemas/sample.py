from typing import Optional, List
from pydantic import Field, validator
from datetime import datetime

from schemas.base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class SampleBase(BaseSchema):
    """
    Base schema for Sample model.
    """
    name: str
    description: Optional[str] = None
    is_active: bool = True
    priority: int = Field(1, ge=1, le=5)
    value: float = 0.0
    notes: Optional[str] = None


class SampleCreate(BaseCreateSchema):
    """
    Schema for creating a new Sample.
    """
    name: str
    description: Optional[str] = None
    is_active: bool = True
    priority: int = Field(1, ge=1, le=5)
    value: float = 0.0
    notes: Optional[str] = None
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        """Validate priority range."""
        if v < 1 or v > 5:
            raise ValueError('Priority must be between 1 and 5')
        return v


class SampleUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing Sample.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    value: Optional[float] = None
    notes: Optional[str] = None
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        """Validate priority range."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Priority must be between 1 and 5')
        return v


class SampleResponse(BaseResponseSchema):
    """
    Schema for Sample response.
    """
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    value: float
    notes: Optional[str]
    last_updated: datetime
