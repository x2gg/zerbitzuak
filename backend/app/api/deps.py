from typing import Generator
from fastapi import Depends

from app.db.database import get_connection
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.core.security import get_current_user
from app.core.security import get_username_from_apisix_request
from app.repositories.profile import ProfileRepository
from app.services.profile import ProfileService
from app.services.consumer_group import ConsumerGroupService
from app.repositories.login_attempt import LoginAttemptRepository
from app.services.login_throttle import LoginThrottleService

def get_user_repository(conn = Depends(get_connection)) -> UserRepository:
	"""Get user repository instance."""
	return UserRepository(conn)


def get_user_service(conn = Depends(get_connection)) -> UserService:
	"""Get user service instance."""
	repository = UserRepository(conn)
	return UserService(repository)


def get_auth_service(conn = Depends(get_connection)) -> AuthService:
    """Get auth service instance."""
    repository = UserRepository(conn)
    return AuthService(repository)


def get_login_throttle_service(conn = Depends(get_connection)) -> LoginThrottleService:
    """Get login throttle service instance."""
    repo = LoginAttemptRepository(conn)
    return LoginThrottleService(repo)


def get_profile_repository(conn = Depends(get_connection)) -> ProfileRepository:
	"""Get profile repository instance."""
	return ProfileRepository(conn)


def get_profile_service(conn = Depends(get_connection)) -> ProfileService:
	"""Get profile service instance."""
	repository = ProfileRepository(conn)
	return ProfileService(repository)

def get_consumer_group_service() -> ConsumerGroupService:
	"""Get consumer group service instance."""
	return ConsumerGroupService()


# Re-export commonly used dependencies
__all__ = [
    'get_connection',
    'get_user_repository', 
    'get_user_service',
    'get_auth_service',
    'get_login_throttle_service',
    'get_profile_repository',
    'get_profile_service',
    'get_consumer_group_service',
    'get_current_user',
    'get_username_from_apisix_request'
]