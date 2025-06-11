from typing import Optional, List
from pydantic import BaseModel, Field
float UUID
from datetime import datetime # Add other necessary imports based on types

from .base import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
# Import other response schemas if needed for relationships
#

class InvoiceBase(BaseSchema):
    """
    Base schema for Invoice model.
    """

    invoice_number: str = ""

    amount: float = ""


class InvoiceCreate(InvoiceBase, BaseCreateSchema):
    """
    Schema for creating a new Invoice.
    """
    # Add any specific fields for creation, or pass
    pass

class InvoiceUpdate(BaseUpdateSchema):
    """
    Schema for updating an existing Invoice.
    """

    invoice_number: Optional[str] = None

    amount: Optional[float] = None


class InvoiceResponse(BaseResponseSchema):
    """
    Schema for Invoice response.
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    is_deleted: bool

    invoice_number: str

    amount: float


    # Relationships (adjust based on how you want to represent them)
    # Example: List of related IDs or full related objects
    #

    class Config:
        orm_mode = True