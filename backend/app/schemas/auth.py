from pydantic import BaseModel, Field, EmailStr

from app.core.config import settings


class UserLogin(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	password: str = Field(min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)
	
class FederatedLogin(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	email: EmailStr = Field(max_length=settings.EMAIL_MAX_LENGTH)
	password: str = Field(min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)

class Token(BaseModel):
	access_token: str = Field(pattern=settings.ACCESS_TOKEN_PATTERN, max_length=settings.ACCESS_TOKEN_MAX_LENGTH)
	# token_type: str = Field("bearer")
	status: str

class TokenPayload(BaseModel):
	sub: str
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	exp: int
	iat: int