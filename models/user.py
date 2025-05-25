from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from models.base import BaseModel

user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", UUID, ForeignKey("user.id"), primary_key=True),
    Column("role_id", UUID, ForeignKey("role.id"), primary_key=True),
)

class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        email: User's email address (unique)
        hashed_password: Securely hashed password (nullable for OAuth users)
        is_active: Whether the user account is active
        is_superuser: Whether the user has superuser privileges
        full_name: User's full name
        oauth_accounts: Relationship to OAuthAccount model (one-to-many)
        roles: Relationship to Role model (many-to-many)
    """
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Made nullable for OAuth users
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    full_name = Column(String, nullable=True)
    
    # OAuth accounts relationship
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    
    # Roles relationship
    roles = relationship("Role", secondary="user_roles", back_populates="users", lazy="joined")
    
    @property
    def has_password(self) -> bool:
        return self.hashed_password is not None
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
