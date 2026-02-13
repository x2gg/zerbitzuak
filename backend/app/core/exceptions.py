from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class UserNotFoundException(HTTPException):
	def __init__(self, user_id: int):
		super().__init__(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"User with id {user_id} not found"
		)


class TooManyLoginAttemptsException(HTTPException):
	def __init__(self, retry_after_seconds: int):
		super().__init__(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail="Too many failed login attempts. Try again later."
			# ,
			# headers={"Retry-After": str(retry_after_seconds)}
		)


class PasswordNotSecureException(HTTPException):
	def __init__(self, count: int):
		super().__init__(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"PasswordNotSecure;{count}"
		)


class UserAlreadyExistsException(HTTPException):
	def __init__(self, username: str):
		super().__init__(
			status_code=status.HTTP_409_CONFLICT,
			detail=f"User with username {username} already exists"
		)

class EmailAlreadyExistsException(HTTPException):
	def __init__(self, email: str):
		super().__init__(
			status_code=status.HTTP_409_CONFLICT,
			detail=f"The email {email} is already associated with an existing user."
		)


class InvalidCredentialsException(HTTPException):
	def __init__(self):
		super().__init__(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid username or password",
			headers={"WWW-Authenticate": "Bearer"}
		)


class UserDisabledException(HTTPException):
	def __init__(self):
		super().__init__(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="User account is disabled"
		)


class APISIXException(HTTPException):
	def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
		super().__init__(
			status_code=status_code,
			detail=f"APISIX error: {detail}"
		)


class DatabaseException(HTTPException):
	def __init__(self, detail: str):
		super().__init__(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Database error: {detail}"
		)

class ProfileNotFoundException(HTTPException):
	def __init__(self, profile_id: str):
		super().__init__(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Profile '{profile_id}' not found"
		)

class ProfileAlreadyExistsException(HTTPException):
	def __init__(self, profile_type: str):
		super().__init__(
			status_code=status.HTTP_409_CONFLICT,
			detail=f"Profile '{profile_type}' already exists"
		)