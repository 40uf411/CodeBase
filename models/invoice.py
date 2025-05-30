from sqlalchemy import Column, String, Boolean, ForeignKey, Table, Integer, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid_pkg as uuid
import base_model

import BaseModel

# Association table for Many-to-Many relationships (if any)


class Invoice(BaseModel):
    """
    Represents a customer invoice.

    Attributes:

        invoice_number: Unique invoice number

        amount: Total amount of the invoice


    """

    invoice_number = Column(String,
                          unique=True,

                          nullable=False,
                          default=)

    amount = Column(Float,


                          nullable=False,
                          default=)


    # Relationships


    def __repr__(self) -> str:
        return f"Invoice <{self.id}>"