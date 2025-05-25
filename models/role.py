from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Role(BaseModel):
    """
    Role model for role-based access control.
    
    Attributes:
        name: Role name (unique)
        description: Role description
        users: Relationship to User model (many-to-many)
        privileges: Relationship to Privilege model (many-to-many)
    """
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    users = relationship("User", secondary="user_roles", back_populates="roles", lazy="joined")
    privileges = relationship("Privilege", secondary="role_privileges", back_populates="roles", lazy="joined")
    
    # Relationships will be defined in the actual implementation
    # users = relationship("User", secondary="user_roles", back_populates="roles")
    # privileges = relationship("Privilege", secondary="role_privileges", back_populates="roles")
    
    def __repr__(self) -> str:
        return f"<Role {self.name}>"
