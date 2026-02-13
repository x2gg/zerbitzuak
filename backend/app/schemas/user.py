from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from app.core.config import settings


class UserBase(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	email: EmailStr = Field(max_length=settings.EMAIL_MAX_LENGTH)
	u_status: str = Field(default='pending')
	u_type: str = Field(default=settings.DEFAULT_U_TYPE)
	isFederated: bool = Field(default=False)
	email_verified: bool = Field(default=False)


class UserCreate(UserBase):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	password: str = Field(min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)
	api_key: Optional[str] = Field(default=None, min_length=settings.API_KEY_LENGTH, max_length=settings.API_KEY_LENGTH, pattern=settings.API_KEY_PATTERN)
	u_type: str = Field(default=settings.DEFAULT_U_TYPE)
	u_status: str = Field(default="pending")
	isFederated: bool = Field(default=False)


class UserUpdate(BaseModel):
	username: Optional[str] = Field(None, min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	password: Optional[str] = Field(None, min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)
	email: Optional[EmailStr] = Field(None, max_length=settings.EMAIL_MAX_LENGTH)
	api_key: Optional[str] = Field(None, min_length=settings.API_KEY_LENGTH, max_length=settings.API_KEY_LENGTH, pattern=settings.API_KEY_PATTERN)
	u_status: Optional[str] = None
	u_type: Optional[str] = None
	isFederated: Optional[bool] = None


class User(UserBase):
	id: int
	api_key: Optional[str] = None
	
	class Config:
		from_attributes = True


class UserInDB(User):
	hashed_password: str


class UserProfile(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
	email: EmailStr = Field(max_length=settings.EMAIL_MAX_LENGTH)
	api_key_preview: Optional[str] = None
	email_verified: Optional[bool] = None
	u_status: str

class SendVerificationRequest(BaseModel):
	username: str = Field(min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)

class SendVerificationResponse(BaseModel):
	success: bool
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)
	email: Optional[str] = None
	error: Optional[str] = None

class EmailVerificationRequest(BaseModel):
    code: str = Field(
        min_length=settings.EMAIL_VERIFICATION_CODE_LENGTH,
        max_length=settings.EMAIL_VERIFICATION_CODE_LENGTH,
        pattern=r'^\d+$',
        description="Código de verificación numérico"
    )

class EmailVerificationResponse(BaseModel):
	verified: bool
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)

class GenerateApiKeyResponse(BaseModel):
	success: bool
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)
	api_key: Optional[str] = None
	api_key_preview: Optional[str] = None
	error: Optional[str] = None


class SendPasswordRecoveryRequest(BaseModel):
	email: EmailStr = Field(max_length=settings.EMAIL_MAX_LENGTH)


class SendPasswordRecoveryResponse(BaseModel):
	success: bool
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)
	email: Optional[EmailStr] = Field(None, max_length=settings.EMAIL_MAX_LENGTH)
	error: Optional[str] = None


class PasswordRecoveryRequest(BaseModel):
	code: str = Field(min_length=settings.PASSWORD_RECOVERY_CODE_LENGTH, max_length=settings.PASSWORD_RECOVERY_CODE_LENGTH)
	password: str = Field(min_length=settings.PASSWORD_MIN_LENGTH, max_length=settings.PASSWORD_MAX_LENGTH)


class PasswordRecoveryResponse(BaseModel):
	success: bool
	message: str = Field(max_length=settings.MESSAGE_MAX_LENGTH)
	error: Optional[str] = None