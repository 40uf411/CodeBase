from pydantic import BaseModel

class LoggingSettingUpdate(BaseModel):
    is_enabled: bool

class LoggingSettingResponse(BaseModel):
    setting_name: str
    is_enabled: bool
    description: Optional[str] = None # Using Optional from typing

    class Config:
        orm_mode = True
