from pydantic import BaseModel, Field
from typing import Optional
from app.core.config import settings

class ProfileBase(BaseModel):
	u_type: str
	count: int
	time_window: int
	rejected_code: int
	rejected_msg: str
	policy: str
	show_limit_quota_header: bool


class ProfileCreate(ProfileBase):
	pass


class ProfileUpdate(BaseModel):
	u_type: Optional[str] = None
	count: Optional[int] = None
	time_window: Optional[int] = None
	rejected_code: Optional[int] = None
	rejected_msg: Optional[str] = Field(None, max_length=settings.MESSAGE_MAX_LENGTH)
	policy: Optional[str] = None
	show_limit_quota_header: Optional[bool] = None


class Profile(ProfileBase):
	id: str
	
	class Config:
		from_attributes = True