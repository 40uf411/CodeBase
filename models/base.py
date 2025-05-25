import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from core.database import Base


class BaseModel(Base):
    """
    Base model with common fields and functionality.
    
    Features:
    - UUID primary key
    - Timestamp fields (created_at, updated_at, deleted_at)
    - Soft delete functionality
    - Streamable flag for real-time updates
    """
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name."""
        return cls.__name__.lower()
    
    # UUID primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def soft_delete(self) -> None:
        """Mark record as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the model instance with optional attributes."""
        super().__init__(**kwargs)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.deleted_at = None
        self.is_deleted = False
        self.id = uuid.uuid4()
        self.__dict__.update(kwargs)
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})>"

    def __str__(self) -> str:
        """String representation of the model instance."""
        return f"{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality of two model instances."""
        if not isinstance(other, BaseModel):
            return NotImplemented
        return self.id == other.id
    
    def __ne__(self, other: Any) -> bool:
        """Check inequality of two model instances."""
        if not isinstance(other, BaseModel):
            return NotImplemented
        return self.id != other.id
    
    def __hash__(self) -> int:
        """Hash function for model instances."""
        return hash(self.id)
