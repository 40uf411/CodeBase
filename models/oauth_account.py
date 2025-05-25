from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from models.base import BaseModel


class OAuthAccount(BaseModel):
    """
    OAuth account model for third-party authentication.
    
    Attributes:
        provider: OAuth provider name (e.g., 'google', 'facebook')
        provider_user_id: User ID from the provider
        access_token: OAuth access token
        expires_at: Token expiration timestamp
        refresh_token: OAuth refresh token
        user_id: Relationship to User model
        user: User relationship
    """
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=False, unique=True)
    access_token = Column(String, nullable=True)
    expires_at = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    
    # Relationship to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    user = relationship("User", back_populates="oauth_accounts")
    
    def __repr__(self) -> str:
        return f"<OAuthAccount {self.provider}:{self.provider_user_id}>"
