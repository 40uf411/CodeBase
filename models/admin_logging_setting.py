import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from models.base import Base # Assuming 'models.base' contains your declarative_base()

class AdminLoggingSetting(Base):
    __tablename__ = "admin_logging_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_name = Column(String, unique=True, index=True, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AdminLoggingSetting(setting_name='{self.setting_name}', is_enabled={self.is_enabled})>"
