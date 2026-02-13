from typing import List, Optional, Dict, Any, Generator
import logging
from datetime import datetime, timedelta
import secrets
import mysql.connector

from app.repositories.user import UserRepository
from app.services.apisix import APISIXService
from app.services.email import EmailService
from app.schemas.user import (
	User, UserCreate, UserUpdate, UserProfile, GenerateApiKeyResponse,
	SendPasswordRecoveryRequest, SendPasswordRecoveryResponse,
	PasswordRecoveryRequest, PasswordRecoveryResponse
)
from app.schemas.consumer import ConsumerCreate
from app.core.exceptions import (
	UserNotFoundException, UserAlreadyExistsException, 
	EmailAlreadyExistsException, DatabaseException,
	PasswordNotSecureException
)
from app.services.consumer_group import ConsumerGroupService
from app.core.config import settings
from app.db.database import get_db
from app.core.security import check_pwd_security

import subprocess

from app.core.config import settings
DEFAULT_U_TYPE = settings.DEFAULT_U_TYPE


# Configure logger
logger = logging.getLogger(__name__)

class UserService:
	"""Service for user management operations."""
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository
		self.apisix_service = APISIXService()
		self.consumer_group_service = ConsumerGroupService()
	
	async def create_user(self, user_data: UserCreate) -> User:
		"""Create a new user in database and its APISIX consumer."""
		# Check if user already exists
		existing_user = self.user_repository.get_by_username(user_data.username)
		if existing_user:
			raise UserAlreadyExistsException(user_data.username)

		# Check if email already exists
		existing_user = self.user_repository.get_by_email(user_data.email)
		if existing_user:
			raise EmailAlreadyExistsException(user_data.email)

		# Check if password is secure
		is_secure, count = check_pwd_security(user_data.password)
		if not is_secure:
			raise PasswordNotSecureException(count)

		# Prepare database user data
		db_user_data = {
			"username": user_data.username,
			"email": user_data.email,
			"u_type": user_data.u_type or settings.DEFAULT_U_TYPE,
			"u_status": user_data.u_status,
			"isFederated": user_data.isFederated,
			"api_key_preview": None,
			"email_verified": 1 if user_data.u_status == 'active' else 0,
			"created_at": datetime.now(),
			"updated_at": datetime.now()
		}

		try:
			# Ensure profile group exists for this u_type
			if not self.apisix_service.profile_group_exists(db_user_data["u_type"]):
				raise DatabaseException(f"Failed to ensure profile group exists for {db_user_data['u_type']}")
			
			# Create user in database
			user_id = self.user_repository.create(db_user_data)

			if not user_id:
				raise DatabaseException("Failed to create user")
			
			# Create APISIX consumer
			consumer_data = ConsumerCreate(
				username=user_data.username,
				password=user_data.password,
				u_type=user_data.u_type or settings.DEFAULT_U_TYPE
			)
			self.apisix_service.create_consumer(consumer_data)
			
			# Get the created user
			created_user = self.user_repository.get_by_id(user_id)
			if not created_user:
				raise DatabaseException("Failed to retrieve created user")
				
			return User(**created_user)
		
		except Exception as e:
			if user_id:
				# If APISIX consumer creation fails, we should clean up the database user
				await self.delete_user(user_id)

			logger.error(f"Error creating user: {str(e)}")
			if not isinstance(e, (UserAlreadyExistsException, EmailAlreadyExistsException, DatabaseException)):
				raise DatabaseException("An error occurred while creating the user")
			raise e
		
		finally:
			self.user_repository.close()

	async def send_password_recovery(self, email: str) -> Dict[str, Any]:
		"""Initiate password recovery by email without revealing account existence."""
		try:
			user = self.user_repository.get_user_minimal_by_email(email)
			# Always respond success to avoid user enumeration
			generic_response = {
				"success": True,
				"message": "If the email exists and is verified, a recovery link has been sent. Note that this functionality is not available for federated users."
			}

			if not user:
				return generic_response

			if user.get("isFederated") or user.get('u_status') != "active":
				return generic_response

			if not self.user_repository.can_send_password_recovery(email):
				# Still send generic response
				return generic_response

			# Generate secure token and expiry
			token = secrets.token_urlsafe(32)
			expires_at = datetime.now() + timedelta(minutes=settings.PASSWORD_RECOVERY_EXPIRE_MINUTES)

			if not self.user_repository.save_password_recovery_token(email, token, expires_at):
				# Do not leak info, still generic
				return generic_response

			self.user_repository.commit()

			# Build recovery link and send email
			recovery_link = f"{settings.PASSWORD_RESET_BASE_URL}?t={token}"
			email_service = EmailService()
			await email_service.send_password_recovery_email(
				to_email=email,
				username=user.get('username'),
				recovery_link=recovery_link
			)

			return generic_response
		except Exception as e:
			self.user_repository.rollback()
			logger.error(f"Error initiating password recovery: {str(e)}", exc_info=True)
			# Still do not reveal details
			return {
				"success": True,
				"message": "If the email exists and is verified, a recovery link has been sent."
			}
		finally:
			self.user_repository.close()

	async def reset_password_with_token(self, code: str, new_password: str) -> Dict[str, Any]:
		"""Validate code and reset password in APISIX consumer."""
		try:
			# Validate code
			email_result = self.user_repository.search_recovery_email(code)
			if not email_result:
				return {
					"success": False,
					"message": "Invalid or expired code"
				}
			email = email_result.get('email')
			if not email:
				return {
					"success": False,
					"message": "Invalid or expired code"
				}
			if not self.user_repository.validate_recovery_code(email, code):
				return {
					"success": False,
					"message": "Invalid or expired code"
				}

			user = self.user_repository.get_user_minimal_by_email(email)
			if not user or user.get('u_status') == 'disabled':
				return {
					"success": False,
					"message": "Invalid or expired code"
				}

			# Update password via APISIX and our update flow
			updates = UserUpdate(password=new_password)
			await self.update_user(user_id=user['id'], user_update=updates)

			# Clear code
			self.user_repository.clear_recovery_code(email)
			self.user_repository.commit()

			return {
				"success": True,
				"message": "Password has been reset successfully"
			}
		except Exception as e:
			self.user_repository.rollback()
			logger.error(f"Error resetting password: {str(e)}", exc_info=True)
			return {
				"success": False,
				"message": "Failed to reset password"
			}
		finally:
			self.user_repository.close()
	
	async def get_user(self, user_id: int) -> User:
		"""Get a user by ID."""
		try:
			user = self.user_repository.get_by_id(user_id)
			if not user:
				raise UserNotFoundException(user_id)
			return User(**user)
		except Exception as e:
			logger.error(f"Error getting user {user_id}: {str(e)}")
			if not isinstance(e, UserNotFoundException):
				raise DatabaseException("An error occurred while retrieving the user")
			raise
	
	async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
		"""Update a user and its APISIX consumer if needed."""
		empty_update = not any(
			value is not None
			for field, value in user_update.dict().items()
		)

		if empty_update:
			raise ValueError("No fields to update")

		# Get existing user
		user = self.user_repository.get_by_id(user_id)
		if not user:
			raise UserNotFoundException(user_id)
		
		consumer_updates = {}
		user_updates = {}
		consumer_relevant_fields = ['username', 'password', 'u_type', 'api_key']

		for field, value in user_update.dict(exclude_unset=True).items():
			if field in consumer_relevant_fields:
				consumer_updates[field] = value
				if field == 'password':
					pass
				elif field == 'api_key':
					user_updates['api_key_preview'] = value[:3] + '...' + value[-3:]
				else:
					user_updates[field] = value
			else:
				user_updates[field] = value
		# Update consumer if needed
		if consumer_updates:
			self.apisix_service.update_consumer(user['username'], consumer_updates)

		# Update user in database
		if user_updates:
			self.user_repository.update(user_id, user_updates)
			self.user_repository.commit()
		
		return User(**user)

		

	def _create_consumer_config_for_groups(
		self, 
		current_consumer: Dict[str, Any], 
		new_username: Optional[str] = None,
		new_password: Optional[str] = None,
		new_api_key: Optional[str] = None,
		u_type: str = settings.DEFAULT_U_TYPE
	) -> Dict[str, Any]:
		"""Create consumer config for use with groups (no individual limit-count)."""
		from app.core.security import get_password_hash
		
		existing_plugins = current_consumer.get("plugins", {})
		
		# Base configuration
		merged_consumer = {
			"username": new_username or current_consumer.get("username"),
			"group_id": u_type,  # Assign to group
			"plugins": {}
		}
		
		# Handle jwt-auth
		if new_password:
			hashed_password = get_password_hash(new_password)
			merged_consumer["plugins"]["jwt-auth"] = {
				"key": merged_consumer["username"],
				"secret": hashed_password,
				"algorithm": settings.JWT_ALGORITHM
			}
		elif "jwt-auth" in existing_plugins:
			merged_consumer["plugins"]["jwt-auth"] = existing_plugins["jwt-auth"]
			merged_consumer["plugins"]["jwt-auth"]["key"] = merged_consumer["username"]
		
		# Handle key-auth
		if new_api_key:
			merged_consumer["plugins"]["key-auth"] = {"key": new_api_key}
		elif "key-auth" in existing_plugins:
			merged_consumer["plugins"]["key-auth"] = existing_plugins["key-auth"]
		
		# Preserve other plugins (but NOT limit-count, as it comes from the group)
		for plugin_name, plugin_config in existing_plugins.items():
			if plugin_name not in ["jwt-auth", "limit-count", "key-auth"]:
				merged_consumer["plugins"][plugin_name] = plugin_config
		
		return merged_consumer
	
	async def delete_user(self, user_id: int) -> Dict[str, str]:
		"""Delete a user and its APISIX consumer."""
		# Get user
		user = self.user_repository.get_by_id(user_id)
		if not user:
			raise UserNotFoundException(user_id)
		
		username = user['username']
		
		try:
			# Delete from APISIX first
			self.apisix_service.delete_consumer(username)
			
			# Delete from database
			self.user_repository.delete(user_id)
			self.user_repository.commit()
			
			return {"message": f"User {user_id} deleted"}
			
		except Exception as e:
			self.user_repository.rollback()
			raise e
		finally:
			self.user_repository.close()
	
	async def list_users(
		self,
		u_type: Optional[str] = None,
		u_status: Optional[str] = None,
		email_contains: Optional[str] = None,
		is_federated: Optional[bool] = None,
		email_verified: Optional[bool] = None
	) -> List[User]:
		"""List users with optional filters."""
		users = self.user_repository.list_users(
			u_type=u_type,
			u_status=u_status,
			email_contains=email_contains,
			is_federated=is_federated,
			email_verified=email_verified
		)
		return [User(**user) for user in users]

	async def get_user_profile_by_username(self, username: str) -> UserProfile:
		"""Get user profile by username."""
		profile_data = self.user_repository.get_user_profile(username)
		if not profile_data:
			raise HTTPException(
				status_code=404, 
				detail="User profile not found or account is disabled"
			)
		return UserProfile(**profile_data)

	async def send_verification_email(self, username: str) -> Dict[str, Any]:
		"""Send verification email to user."""
		try:
			# Check if user exists and get their email
			user_status = self.user_repository.get_user_email_status(username)
			
			if not user_status:
				return {
					"success": False,
					"message": "User not found"
				}
			
			# Check if already verified
			if user_status.get('email_verified'):
				return {
					"success": False,
					"message": "Email already verified",
				}
			
			# Check if user is disabled
			if user_status.get('u_status') == 'disabled':
				return {
					"success": False,
					"message": "User account is disabled"
				}
			
			# Check cooldown period
			if not self.user_repository.can_send_verification(username):
				return {
					"success": False,
					"message": f"Please wait {settings.VERIFICATION_COOLDOWN_MINUTES} minutes before requesting another verification code."
				}
			
			# Generate and save verification code
			email_service = EmailService()
			verification_code = email_service.generate_verification_code()
			
			if not self.user_repository.save_verification_code(username, verification_code):
				raise DatabaseException("Failed to save verification code")
			
			self.user_repository.commit()
			
			# Send email
			result = await email_service.send_verification_email(
				user_status['email'],
				username,
				verification_code
			)
			
			return result
			
		except Exception as e:
			self.user_repository.rollback()
			logger.error(f"Error sending verification email: {str(e)}")
			return {
				"success": False,
				"message": "Failed to send verification email",
				"error": str(e)
			}
		finally:
			self.user_repository.close()

	async def verify_email(self, username: str, code: str) -> bool:
		"""Verify user's email with provided code and update user status to 'active' if currently 'pending'."""
		try:
			# Check if user status is 'pending'
			current_status = self.user_repository.get_user_status(username)
			if current_status != 'pending':
				return False
			
			# First increment attempts
			self.user_repository.increment_verification_attempts(username)
			
			# Try to verify
			success = self.user_repository.verify_email_code(username, code)
			
			# If verification was successful, update user status to 'active'
			if success:
				user = self.user_repository.get_by_username(username)
				if user:
					self.user_repository.update(user['id'], {'u_status': 'active'})
			
			self.user_repository.commit()
			return success
			
		except Exception as e:
			self.user_repository.rollback()
			raise e
		finally:
			self.user_repository.close()

	async def get_verification_status(self, username: str) -> Dict[str, Any]:
		"""Get user's verification status."""
		user_status = self.user_repository.get_user_email_status(username)
		
		if not user_status:
			raise UserNotFoundException(0)  # We don't have the ID here
		
		return {
			"username": username,
			"email_verified": user_status.get("email_verified", False),
			"has_pending_code": bool(
				user_status.get("verification_code_expires") and 
				user_status["verification_code_expires"] > datetime.now()
			)
		}
	
	async def generate_apiKey(self, username: str) -> Dict[str, Any]:
		"""Generate a new API key for the user.
		
		Args:
			username: The username to generate the API key for
			
		Returns:
			Dict containing the API key, preview, and status
			
		Raises:
			DatabaseException: If there's an error generating the key
		"""
		# Generate a secure random API key
		api_key = subprocess.check_output(["openssl", "rand", "-base64", "24"]).decode().strip()
		api_key_preview = api_key[:3] + '...' + api_key[-3:]

		# Get the user details
		user = self.user_repository.get_by_username(username)

		try:
			user_data = UserUpdate(api_key=api_key)
			updated_user = await self.update_user(user_id=user.get("id"), user_update=user_data)
			
			# Save the preview and update the user
			# success = self.user_repository.save_apiKey_preview(username, api_key_preview)
			if not updated_user:
				return {
					"success": False,
					"message": "Failed to generate API key",
					"api_key": None,
					"api_key_preview": None,
					"error": "Failed to save API key preview"
				}
			
			if not user:
				return {
					"success": False,
					"message": "User not found",
					"api_key": None,
					"api_key_preview": None,
					"error": "User not found"
				}
			
			return {
				"success": True,
				"message": "API key generated successfully",
				"api_key": api_key,
				"api_key_preview": api_key_preview,
				"error": None
			}
			
		except subprocess.CalledProcessError as e:
			error_msg = f"Failed to generate secure random data: {str(e)}"
			logger.error(error_msg)
			raise DatabaseException(error_msg)
		except Exception as e:
			error_msg = f"Unexpected error generating API key: {str(e)}"
			logger.error(error_msg, exc_info=True)
			raise DatabaseException(error_msg)