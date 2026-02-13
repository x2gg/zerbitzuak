import os
from typing import List, Optional
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks

from app.api.deps import get_user_service, get_current_user, get_username_from_apisix_request
from app.schemas.user import (
	User, UserCreate, UserUpdate, UserProfile,
	SendVerificationRequest, SendVerificationResponse,
	EmailVerificationRequest, EmailVerificationResponse
)
from app.services.user import UserService, GenerateApiKeyResponse
from app.core.security import get_username_from_apisix_request, ensure_admin_request
from app.core.exceptions import (
	UserAlreadyExistsException,
	EmailAlreadyExistsException,
	UserNotFoundException,
	DatabaseException
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=User, include_in_schema=False)
async def create_user(
	user: UserCreate,
	user_service: UserService = Depends(get_user_service)
) -> User:
	"""
	Create a new user.
	
	This will also create the corresponding APISIX consumer.
	"""

	return await user_service.create_user(user)


@router.get("/", response_model=List[User], include_in_schema=False)
async def list_users(
	request: Request,
	u_type: Optional[str] = None,
	u_status: Optional[str] = None,
	email_contains: Optional[str] = None,
	is_federated: Optional[bool] = None,
	email_verified: Optional[bool] = None,
	user_service: UserService = Depends(get_user_service)
) -> List[User]:
	"""
	List users with optional filters.
	
	- **u_type**: Filter by user type (basic, pro)
	- **u_status**: Filter by status (active, pending, disabled)
	- **email_contains**: Filter by email containing string
	- **is_federated**: Filter by federation status
	- **email_verified**: Filter by verification status
	"""

	ensure_admin_request(request)

	return await user_service.list_users(
		u_type=u_type,
		u_status=u_status,
		email_contains=email_contains,
		is_federated=is_federated,
		email_verified=email_verified
	)


@router.get("/profile", response_model=UserProfile)
async def get_my_profile(
	request: Request,
	user_service: UserService = Depends(get_user_service)
) -> UserProfile:
	"""
	Get authenticated user's profile.
	
	Security: Only returns information of the requesting user.
	GDPR Compliant: Data minimization principle.
	
	Returns:
		- username: Username
		- email: User email
		- api_key_preview: API key preview (if exists)
	
	Raises:
		HTTPException: If user is not authenticated or an error occurs
	"""
	try:

		# ensure_admin_request(request)
		username = get_username_from_apisix_request(request)

		# Get the full user profile
		user = await user_service.get_user_profile_by_username(username)
		if not user:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found"
			)
			
		return user
	except Exception as e:
		logger.error(f"Error getting user profile: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="An error occurred while retrieving the user profile"
		)


@router.get("/send-verification", response_model=SendVerificationResponse, include_in_schema=False)
async def send_verification_email(
	request: Request,
	user_service: UserService = Depends(get_user_service)
) -> SendVerificationResponse:
	"""
	Send verification email to user.
	
	This endpoint can be called:
	- After user registration
	- When user requests a new code
	- From external services
	
	Rate limited to once every 2 minutes per user.
	"""
	# Extract authenticated user from APISIX headers
	username = get_username_from_apisix_request(request)

	result = await user_service.send_verification_email(username)
	
	# For security reasons, do not reveal the email if there was an error
	if not result.get("success"):
		result.pop("email", None)
	
	return SendVerificationResponse(**result)

@router.post("/verify-email", response_model=EmailVerificationResponse, include_in_schema=False)
async def verify_email(
	request: Request,
	verification_data: EmailVerificationRequest,
	user_service: UserService = Depends(get_user_service)
) -> EmailVerificationResponse:
	"""
	Verify user's email with the provided code.
	
	Limited to 5 attempts per code.
	"""
	# Extract authenticated user from APISIX headers
	username = get_username_from_apisix_request(request)

	success = await user_service.verify_email(
		username,
		verification_data.code
	)
	
	if success:
		return EmailVerificationResponse(
			verified=True,
			message="Email verified successfully"
		)
	else:
		return EmailVerificationResponse(
			verified=False,
			message="Invalid or expired verification code"
		)

@router.get("/verification-status/{username}", include_in_schema=False)
async def get_verification_status(
	username: str,
	user_service: UserService = Depends(get_user_service)
) -> dict:
	"""Check user's email verification status."""
	return await user_service.get_verification_status(username)


@router.get("/generate-apiKey", response_model=GenerateApiKeyResponse)
async def generate_apiKey(
	request: Request,
	user_service: UserService = Depends(get_user_service)
) -> GenerateApiKeyResponse:
	"""
	Generate a new API key for the user.
	
	This endpoint can be called:
	- After user registration
	- When user requests a new key
	- From external services
	"""
	# Extract authenticated user from APISIX headers
	username = get_username_from_apisix_request(request)

	result = await user_service.generate_apiKey(username)
	if not result.get("success"):
		raise HTTPException(status_code=400, detail="Failed to generate API key")
	return GenerateApiKeyResponse(**result)


@router.get("/{user_id}", response_model=User)
async def read_user(
	request: Request,
	user_id: int,
	user_service: UserService = Depends(get_user_service)
) -> User:
	"""Get a specific user by ID."""

	ensure_admin_request(request)

	return await user_service.get_user(user_id)


@router.put("/{user_id}", response_model=User, include_in_schema=False)
async def update_user(
	request: Request,
	user_id: int,
	user_updates: UserUpdate,
	user_service: UserService = Depends(get_user_service)
) -> User:
	"""
	Update a user.
	
	This will also update the APISIX consumer if necessary.
	
	Args:
		user_id: The ID of the user to update
		user: The updated user data
		
	Returns:
		User: The updated user
		
	Raises:
		HTTPException: If user is not found or an error occurs
	"""

	ensure_admin_request(request)

	try:
		return await user_service.update_user(user_id, user_updates)
	except UserNotFoundException as e:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(e)
		)
	except (DatabaseException, Exception) as e:
		logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="An error occurred while updating the user"
		)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_user(
	request: Request,
	user_id: int,
	user_service: UserService = Depends(get_user_service)
) -> None:
	"""
	Delete a user.
	
	This will also delete the APISIX consumer.
	
	Args:
		user_id: The ID of the user to delete
		
	Raises:
		HTTPException: If user is not found or an error occurs
	"""

	ensure_admin_request(request)

	
	try:
		await user_service.delete_user(user_id)
		return None
	except UserNotFoundException as e:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(e)
		)
	except Exception as e:
		logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="An error occurred while deleting the user"
		)
