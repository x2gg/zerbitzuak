from pydantic import BaseModel, Field
from typing import Optional

from app.core.config import settings

DEFAULT_U_TYPE = settings.DEFAULT_U_TYPE

class ConsumerCreate(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	password: Optional[str] = Field(None, min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)
	api_key: Optional[str] = Field(None, min_length=settings.API_KEY_LENGTH, max_length=settings.API_KEY_LENGTH, pattern=settings.API_KEY_PATTERN)
	u_type: str = DEFAULT_U_TYPE

class ConsumerResponse(BaseModel):
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)