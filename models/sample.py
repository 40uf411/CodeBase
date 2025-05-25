from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime
from sqlalchemy.sql import func

from models.base import BaseModel


class Sample(BaseModel):
    """
    Sample model to demonstrate full functionality.
    
    This is a standalone entity with no foreign keys,
    used to showcase CRUD operations with authorization checks.
    
    Attributes:
        name: Sample name
        description: Sample description
        is_active: Whether the sample is active
        priority: Sample priority (1-5)
        value: Sample numeric value
        notes: Additional notes
        last_updated: Timestamp of last update
    """
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    value = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Sample {self.name}>"
