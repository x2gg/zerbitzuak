import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
	# Database
	DB_HOST: str = "mysql"
	DB_PORT: int = 3306
	DB_USER: str = "api_user"
	DB_PASSWORD: str = "securepassword"
	DB_NAME: str = "user_db"
	DB_POOL_SIZE: int = 5
	
	# JWT
	# JWT_SECRET_KEY: str = "your-secret-key-here"
	JWT_ALGORITHM: str = "HS256"
	JWT_EXPIRATION_HOURS: int = 24

	# SMTP Configuration
	SMTP_HOST: str = os.getenv("SMTP_HOST")
	SMTP_PORT: int = os.getenv("SMTP_PORT")
	SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
	SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
	SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL")
	SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME")
	SMTP_TLS: bool = True
	SMTP_SSL: bool = False
	
	# Email verification
	EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 30
	MAX_EMAIL_RETRY_ATTEMPTS: int = 3
	VERIFICATION_COOLDOWN_MINUTES: int = 5
	
	# Password recovery
	PASSWORD_RECOVERY_EXPIRE_MINUTES: int = 30
	PASSWORD_RESET_BASE_URL: str = os.getenv("WEB_BASE_URL", "https://dev.hitz.eus/nlp_tresnak/")
	
	# APISIX
	APISIX_ADMIN_URL: str = os.getenv("APISIX_ADMIN_URL", "http://apisix:9180/apisix/admin")
	APISIX_ADMIN_KEY: str = os.getenv("APISIX_ADMIN_KEY")
	
	# User limits
	DEFAULT_U_TYPE: str = "basic"
	BASIC_USER_COUNT: int = 10
	BASIC_USER_MSG: str = "Basic user limit exceeded."
	PRO_USER_COUNT: int = 40
	PRO_USER_MSG: str = "Pro user limit exceeded."
	
	# API
	API_V1_STR: str = "/api/v1"
	PROJECT_NAME: str = "Hitz zentroa"
	VERSION: str = "1.0.0"

	# CRUD
	CRUD_ADMIN: str = os.getenv('CRUD_ADMIN', 'admin')

	# Login
	LOGIN_MAX_ATTEMPTS: int = 3
	LOGIN_LOCKOUT_MINUTES: int = 15
	LOGIN_WINDOW_MINUTES: int = 10
	TRUST_PROXY: bool = True
	FORWARDED_FOR_HEADER: str = "X-Forwarded-For"

	# Have I Been Pwned API timeout
	HIBP_TIMEOUT: int = 2
	
	# Validation constraints
	USERNAME_MIN_LENGTH: int = 3
	USERNAME_MAX_LENGTH: int = 64
	
	PASSWORD_MIN_LENGTH: int = 8
	PASSWORD_MAX_LENGTH: int = 64
	PASSWORD_RECOVERY_CODE_LENGTH: int = 32

	EMAIL_MAX_LENGTH: int = 254  # RFC 5321 standard limit
	EMAIL_VERIFICATION_CODE_LENGTH: int = 6

	ACCESS_TOKEN_MAX_LENGTH: int = 2048
	ACCESS_TOKEN_PATTERN: str = r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$'

	API_KEY_LENGTH: int = 32
	API_KEY_PATTERN: str = r'^[A-Za-z0-9+/=]{32}$'

	MESSAGE_MAX_LENGTH: int = 255

	# NLP
	TEXT_MIN_LENGTH: int = 3
	TEXT_MAX_LENGTH: int = 10000
	MAX_FILE_SIZE_MB: int = 1
	
	class Config:
		env_file = ".env"
		case_sensitive = True


settings = Settings()