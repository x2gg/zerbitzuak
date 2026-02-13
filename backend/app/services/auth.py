from typing import Dict, Any
from app.services.apisix import APISIXService
from app.repositories.user import UserRepository
from app.core.exceptions import InvalidCredentialsException, UserDisabledException, APISIXException
from app.schemas.auth import UserLogin, FederatedLogin, Token
from app.schemas.user import UserCreate
from app.services.user import UserService

class AuthService:
	"""Service for authentication operations."""
	
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository
		self.apisix_service = APISIXService()
	
	async def authenticate_user(self, credentials: UserLogin) -> Token:
		"""
		Authenticate a user by:
		1. Verifying they exist in APISIX
		2. Checking credentials are correct
		3. Verifying user is active in database
		"""
		# Check consumer exists in APISIX
		consumer_data = self.apisix_service.get_consumer_by_username(credentials.username)
		if not consumer_data or consumer_data.get("status") == 0:
			raise InvalidCredentialsException()
		
		# Verify credentials in APISIX
		if not self.apisix_service.verify_jwt_auth_credentials(consumer_data, credentials.password):
			raise InvalidCredentialsException()
		
		# Check user status in database
		user_status = self.user_repository.get_user_status(credentials.username)
		if not user_status:
			raise InvalidCredentialsException()
		
		if user_status == 'disabled':
			raise UserDisabledException()
		
		# Generate token
		access_token = self.apisix_service.create_jwt_token(credentials.username, consumer_data)
		
		token_data = {
			"access_token": access_token,
			"token_type": "bearer",
			"status": user_status
		}
		return Token(**token_data)
	
	async def get_federated_token(self, credentials: FederatedLogin) -> Dict[str, Any]:
		"""
		Verify if a federated user is registered in APISIX and the database.
		If not, register the user.
		"""

		user_service = UserService(self.user_repository)

		# Check if user exists in database
		user = self.user_repository.get_by_username(credentials.username)

		if not user:
			# For new federated users, set status to active
			user_status = "active"

			# Create user
			user = UserCreate(
				username=credentials.username,
				email=credentials.email,
				password=credentials.password,
				u_status=user_status,
				isFederated=True
			)
			await user_service.create_user(user)

			# Get consumer data after user creation
			consumer_data = self.apisix_service.get_consumer_by_username(credentials.username)
			if not consumer_data or consumer_data.get("status") == 0:
				raise APISIXException("Failed to retrieve consumer data after user creation")

		else:
			
			# Check user status in database
			user_status = self.user_repository.get_user_status(credentials.username)

			if not user_status:
				raise InvalidCredentialsException()
			
			if user_status == 'disabled':
				raise UserDisabledException()
			
			# Check consumer exists in APISIX
			consumer_data = self.apisix_service.get_consumer_by_username(credentials.username)

			if not consumer_data or consumer_data.get("status") == 0:
				raise APISIXException("Consumer not found in APISIX")
		
		
		# Generate token
		access_token = self.apisix_service.create_jwt_token(credentials.username, consumer_data)
		
		return {
			"access_token": access_token,
			"token_type": "bearer",
			"status": user_status
		}
