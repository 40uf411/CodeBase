from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator

# Type variable for generic schemas
T = TypeVar('T')


class BaseSchema(BaseModel):
    """
    Base Pydantic schema with common fields and functionality.
    """
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseCreateSchema(BaseSchema):
    """
    Base schema for create operations.
    """
    # is_streamable: Optional[bool] = Field(default=False, description="Flag for real-time streaming")
    pass

class BaseUpdateSchema(BaseSchema):
    """
    Base schema for update operations.
    """
    pass


class BaseResponseSchema(BaseSchema):
    """
    Base schema for response models.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    # is_streamable: bool


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Generic schema for paginated responses.
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @validator('pages')
    def validate_pages(cls, v, values):
        """Calculate total pages if not provided."""
        if v is None and 'total' in values and 'size' in values and values['size'] > 0:
            return (values['total'] + values['size'] - 1) // values['size']
        return v
