from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from models.base import BaseModel

# Many-to-many relationship between privileges and roles
role_privileges = Table(
    "role_privileges",
    BaseModel.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True),
    Column("privilege_id", UUID(as_uuid=True), ForeignKey("privilege.id"), primary_key=True),
)


class Privilege(BaseModel):
    """
    Privilege model for role-based access control.
    
    Attributes:
        name: Privilege name (unique)
        description: Privilege description
        entity: Entity this privilege applies to
        action: Action type (read, write, update, delete)
        roles: Relationship to Role model (many-to-many)
    """
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    entity = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    
    # Relationships
    roles = relationship("Role", secondary=role_privileges, back_populates="privileges", lazy="joined")
    
    def __repr__(self) -> str:
        return f"<Privilege {self.name}>"
