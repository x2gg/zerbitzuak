from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, timedelta
import logging

from app.repositories.base import BaseRepository
from app.schemas.user import User
from app.core.config import settings
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
	"""Repository for user operations."""
	
	@property
	def table_name(self) -> str:
		return "user_db.users"
	
	def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
		"""Get a user by ID."""
		query = f"SELECT * FROM {self.table_name} WHERE id = %s"
		try:
			return self.fetch_one(query, (user_id,))
		except Exception as e:
			raise DatabaseException(f"Error fetching user by ID: {e}")
	
	def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
		"""Get a user by username."""
		query = f"SELECT * FROM {self.table_name} WHERE username = %s"
		try:
			return self.fetch_one(query, (username,))
		except Exception as e:
			raise DatabaseException(f"Error fetching user by username: {e}")
	
	def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
		"""Get a user by email."""
		query = f"SELECT * FROM {self.table_name} WHERE email = %s"
		try:
			return self.fetch_one(query, (email,))
		except Exception as e:
			raise DatabaseException(f"Error fetching user by email: {e}")
	
	def create(self, user_data: Dict[str, Any]) -> int:
		"""Create a new user and return the ID."""
		# Get the value of u_status
		u_status = user_data.get("u_status")
		if u_status == 'active':
			user_data['email_verified'] = 1
		
		fields = list(user_data.keys())
		values = list(user_data.values())
		placeholders = ', '.join(['%s'] * len(fields))
		fields_str = ', '.join(fields)
		
		query = f"""
			INSERT INTO {self.table_name} ({fields_str}) 
			VALUES ({placeholders})
		"""
		
		with self._get_cursor() as cursor:
			cursor.execute(query, tuple(values))
			self.connection.commit()
			return cursor.lastrowid
	
	def update(self, user_id: int, user_data: Dict[str, Any]) -> bool:
		"""Update a user."""
		if not user_data:
			return False
		
		fields = []
		values = []
		for field, value in user_data.items():
			if value is not None:
				fields.append(f"{field} = %s")
				values.append(value)
		
		if not fields:
			return False
		
		values.append(user_id)
		query = f"""
			UPDATE {self.table_name} 
			SET {', '.join(fields)} 
			WHERE id = %s
		"""
		with self._get_cursor() as cursor:
			cursor.execute(query, tuple(values))
			return cursor.rowcount > 0
	
	def delete(self, user_id: int) -> bool:
		"""Delete a user."""
		query = f"DELETE FROM {self.table_name} WHERE id = %s"
		with self._get_cursor() as cursor:
			cursor.execute(query, (user_id,))
			return cursor.rowcount > 0
	
	def list_users(
		self, 
		u_type: Optional[str] = None,
		u_status: Optional[str] = None,
		email_contains: Optional[str] = None,
		is_federated: Optional[bool] = None,
		email_verified: Optional[bool] = None
	) -> List[Dict[str, Any]]:
		"""List users with optional filters."""
		query = f"SELECT * FROM {self.table_name} WHERE 1=1"
		params = []
		
		if u_type:
			query += " AND u_type = %s"
			params.append(u_type)
		if u_status:
			query += " AND u_status = %s"
			params.append(u_status)
		if email_contains:
			query += " AND email LIKE %s"
			params.append(f"%{email_contains}%")
		if is_federated is not None:
			query += " AND isFederated = %s"
			params.append(is_federated)
		if email_verified is not None:
			query += " AND email_verified = %s"
			params.append(email_verified)
		result = self.fetch_many(query, tuple(params) if params else None)
		return result
	
	def get_user_status(self, username: str) -> Optional[str]:
		"""Get user status by username."""
		query = f"SELECT u_status FROM {self.table_name} WHERE username = %s"
		try:
			result = self.fetch_one(query, (username,))
			return result.get('u_status') if result else None
		except Exception as e:
			raise DatabaseException(f"Error getting user status: {e}")

	def get_user_profile(self, username: str) -> Dict[str, Any]:
		"""Get user profile with minimal data."""
		query = f"""
			SELECT username, email, api_key_preview, email_verified, u_status
			FROM {self.table_name}
			WHERE username = %s AND u_status != 'disabled'
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (username,))
				result = cursor.fetchone()
				# Convert result to dict before returning since cursor will be closed
				return dict(result) if result else None
		except Exception as e:
			raise DatabaseException(f"Error getting user profile: {e}")
	
	def can_send_verification(self, username: str) -> bool:
		"""Check if enough time has passed since last verification email."""
		query = f"""
			SELECT last_verification_sent 
			FROM {self.table_name} 
			WHERE username = %s
		"""
		try:
			result = self.fetch_one(query, (username,))
			
			if not result or not result.get('last_verification_sent'):
				return True
				
			last_sent = result['last_verification_sent']
			cooldown = timedelta(minutes=5)  # 5 minutes cooldown
			return datetime.now() - last_sent > cooldown
		except Exception as e:
			raise DatabaseException(f"Error checking verification cooldown: {e}")
		
		last_sent = result['last_verification_sent']
		cooldown_time = datetime.now() - timedelta(minutes=settings.VERIFICATION_COOLDOWN_MINUTES)
		
		return last_sent < cooldown_time

	def save_verification_code(self, username: str, code: str) -> bool:
		"""Save verification code for user.
		
		Args:
			username: The username to save the verification code for
			code: The verification code to save
			
		Returns:
			bool: True if the code was saved successfully, False otherwise
			
		Raises:
			DatabaseException: If there's an error executing the query
		"""
		expires_at = datetime.now() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)
		query = f"""
			UPDATE {self.table_name} 
			SET verification_code = %s, 
				verification_code_expires = %s,
				verification_attempts = 0,
				last_verification_sent = NOW()
			WHERE username = %s
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (code, expires_at, username))
				self.connection.commit()
				# For UPDATE queries, rowcount returns the number of rows affected
				return cursor.rowcount > 0
		except Exception as e:
			self.connection.rollback()
			logger.error(f"Error saving verification code for user {username}: {str(e)}")
			raise DatabaseException(f"Error saving verification code: {e}")

	def get_user_email_status(self, username: str) -> Dict[str, Any]:
		"""Get user's email and verification status."""
		query = f"""
			SELECT email, email_verified, verification_code
			FROM {self.table_name}
			WHERE username = %s
		"""
		try:
			result = self.fetch_one(query, (username,))
			if not result:
				raise ValueError("User not found")
			return result
		except Exception as e:
			raise DatabaseException(f"Error getting user email status: {e}")

	def verify_email_code(self, username: str, code: str) -> bool:
		"""Verify email code and mark email as verified."""
		query = f"""
			UPDATE {self.table_name} 
			SET email_verified = 1,
				verification_code = NULL,
				verification_attempts = 0
			WHERE username = %s AND verification_code = %s
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (username, code))
				return cursor.rowcount > 0
		except Exception as e:
			raise DatabaseException(f"Error verifying email code: {e}")

	def increment_verification_attempts(self, username: str) -> None:
		"""Increment failed verification attempts."""
		query = f"""
			UPDATE {self.table_name} 
			SET verification_attempts = verification_attempts + 1
			WHERE username = %s
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (username,))
		except Exception as e:
			raise DatabaseException(f"Error incrementing verification attempts: {e}")

	# ---- Password recovery helpers ----
	def can_send_password_recovery(self, email: str) -> bool:
		"""Check cooldown using last_recovery_sent timestamp."""
		query = f"""
			SELECT last_recovery_sent 
			FROM {self.table_name}
			WHERE email = %s
		"""
		try:
			result = self.fetch_one(query, (email,))
			if not result or not result.get('last_recovery_sent'):
				return True
			last_sent = result['last_recovery_sent']
			cooldown = timedelta(minutes=settings.VERIFICATION_COOLDOWN_MINUTES)
			return datetime.now() - last_sent > cooldown
		except Exception as e:
			raise DatabaseException(f"Error checking recovery cooldown: {e}")

	def save_password_recovery_token(self, email: str, token: str, expires_at: datetime) -> bool:
		"""Save recovery token and timestamps for the user with given email."""
		query = f"""
			UPDATE {self.table_name}
			SET recovery_token = %s,
				recovery_token_expires = %s,
				recovery_attempts = 0,
				last_recovery_sent = NOW()
			WHERE email = %s
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (token, expires_at, email))
				self.connection.commit()
				return cursor.rowcount > 0
		except Exception as e:
			self.connection.rollback()
			logger.error(f"Error saving recovery token for email {email}: {str(e)}")
			raise DatabaseException(f"Error saving recovery token: {e}")

	def search_recovery_email(self, token: str) -> Dict[str, Any]:
		"""Return True if email has matching non-expired token."""
		query = f"""
			SELECT email FROM {self.table_name}
			WHERE recovery_token = %s
			AND recovery_token_expires > NOW()
		"""
		try:
			result = self.fetch_one(query, (token,))
			return result
		except Exception as e:
			raise DatabaseException(f"Error getting email from recovery token: {e}")

	def validate_recovery_code(self, email: str, code: str) -> bool:
		"""Return True if email has matching non-expired code."""
		query = f"""
			SELECT 1 FROM {self.table_name}
			WHERE email = %s
			AND recovery_token = %s
			AND recovery_token_expires > NOW()
		"""
		try:
			result = self.fetch_one(query, (email, code))
			return bool(result)
		except Exception as e:
			raise DatabaseException(f"Error validating recovery token: {e}")

	def clear_recovery_code(self, email: str) -> None:
		"""Clear recovery code fields after successful reset."""
		query = f"""
			UPDATE {self.table_name}
			SET recovery_token = NULL,
				recovery_token_expires = NULL,
				recovery_attempts = 0
			WHERE email = %s
		"""
		try:
			with self._get_cursor() as cursor:
				cursor.execute(query, (email,))
				self.connection.commit()
		except Exception as e:
			self.connection.rollback()
			raise DatabaseException(f"Error clearing recovery code: {e}")

	def get_user_minimal_by_email(self, email: str) -> Optional[Dict[str, Any]]:
		"""Get minimal fields to proceed with recovery by email."""
		query = f"""
			SELECT id, username, email, email_verified, u_status, isFederated
			FROM {self.table_name}
			WHERE email = %s
		"""
		try:
			return self.fetch_one(query, (email,))
		except Exception as e:
			raise DatabaseException(f"Error fetching user by email: {e}")
