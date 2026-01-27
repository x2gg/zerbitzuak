import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import APISIXException
from app.schemas.consumer import ConsumerCreate
from app.services.consumer_group import ConsumerGroupService

from app.core.config import settings

class APISIXService:
	"""Service for APISIX consumer management."""
	
	def __init__(self):
		self.admin_url = settings.APISIX_ADMIN_URL
		self.headers = {
			"X-API-KEY": settings.APISIX_ADMIN_KEY,
			"Content-Type": "application/json"
		}
	
	@property
	def consumer_groups(self) -> ConsumerGroupService:
		"""Access to Consumer Groups service."""
		if not hasattr(self, '_consumer_groups'):
			self._consumer_groups = ConsumerGroupService()
		return self._consumer_groups
	
	def get_consumer_by_username(self, username: str) -> Optional[Dict[str, Any]]:
		"""Get consumer from APISIX by username."""
		try:
			url = f"{self.admin_url}/consumers/{username}"
			response = requests.get(url, headers=self.headers, timeout=10)
			if response.status_code == 200:
				data = response.json()
				return data.get("value")
			elif response.status_code == 404:
				# Consumer not found
				return None
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def create_consumer(self, consumer: ConsumerCreate) -> bool:
		"""Create a new consumer in APISIX."""
		try:
			hashed_password = get_password_hash(consumer.password)
			
			# Prepare consumer data
			consumer_data = {
				"username": consumer.username,
				"plugins": {
					"jwt-auth": {
						"key": consumer.username,
						"secret": hashed_password,
						"algorithm": settings.JWT_ALGORITHM
					}
				},
				"group_id": consumer.u_type
			}

			# Create consumer
			url = f"{self.admin_url}/consumers/{consumer.username}"
			response = requests.put(url, headers=self.headers, json=consumer_data, timeout=20)
			
			if response.status_code not in [200, 201]:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
			
			return True
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")

	def update_consumer(self, username: str, data_to_update: Dict[str, Any]) -> bool:
		try:
			# Check data_to_update is not empty
			if not data_to_update:
				return False

			# 1. Get consumer data
			get_response = requests.get(
				f"{self.admin_url}/consumers/{username}",
				headers=self.headers,
				timeout=10
			)
			
			if get_response.status_code != 200:
				return False
				
			current_data = get_response.json()["value"]
			
			# 2. Update specific fields
			old_username = current_data.get("username")
			new_username = data_to_update.get("username")
			if new_username:
				current_data["username"] = new_username
				# Update key in jwt-auth if plugin exists
				if "plugins" in current_data and "jwt-auth" in current_data["plugins"]:
					current_data["plugins"]["jwt-auth"]["key"] = new_username
				
			# Accept either 'group' or 'u_type' to update group assignment
			if "group" in data_to_update:
				current_data["group_id"] = data_to_update["group"]
			if "u_type" in data_to_update:
				current_data["group_id"] = data_to_update["u_type"]

			if "api_key" in data_to_update:
				# Update plugin key-auth if exists
				if "plugins" not in current_data:
					current_data["plugins"] = {}
				current_data["plugins"]["key-auth"] = {
					"key": data_to_update["api_key"]
				}
			
			if "password" in data_to_update:
				# Update plugin jwt-auth
				if "plugins" not in current_data:
					current_data["plugins"] = {}
				
				hashed_password = get_password_hash(data_to_update["password"])
				current_data["plugins"]["jwt-auth"] = {
					"key": current_data["username"],
					"secret": hashed_password,
					"algorithm": settings.JWT_ALGORITHM
				}
			
			# 3. Make PUT with updated configuration
			# If username changed, PUT to the new key path and remove the old one
			target_username = new_username if new_username else username

			# Remove APISIX-managed read-only fields that must not be sent back
			for ro_field in ("create_time", "update_time"):
				if ro_field in current_data:
					current_data.pop(ro_field, None)

			put_response = requests.put(
				f"{self.admin_url}/consumers/{target_username}",
				headers=self.headers,
				json=current_data,
				timeout=20
			)
			
			if put_response.status_code not in [200, 201]:
				raise APISIXException(f"Status {put_response.status_code}: {put_response.text}")
			
			# Clean up the old key if we renamed and the old key differs
			if new_username and new_username != old_username and old_username != target_username:
				try:
					requests.delete(
						f"{self.admin_url}/consumers/{old_username}",
						headers=self.headers,
						timeout=10
					)
				except requests.RequestException:
					# Non-fatal: the new consumer is already updated; old key cleanup failed
					pass
			
			return True
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
		except Exception as e:
			# Do not silently swallow errors
			raise APISIXException(str(e))

	
	def delete_consumer(self, username: str) -> bool:
		"""Delete a consumer from APISIX."""
		try:
			url = f"{self.admin_url}/consumers/{username}"
			response = requests.delete(url, headers=self.headers, timeout=10)
			
			if response.status_code in [200, 404]:
				return True
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def verify_jwt_auth_credentials(self, consumer_data: Dict[str, Any], password: str) -> bool:
		"""Verify JWT auth credentials."""
		jwt_auth = consumer_data.get("plugins", {}).get("jwt-auth")
		if not jwt_auth:
			return False
		
		stored_secret = jwt_auth.get("secret") or jwt_auth.get("password")
		if not stored_secret:
			return False
		
		return verify_password(password, stored_secret)
	
	def create_jwt_token(self, username: str, consumer_data: Dict[str, Any]) -> str:
		"""Create JWT token using user's specific secret from APISIX."""
		jwt_auth_config = consumer_data.get("plugins", {}).get("jwt-auth", {})
		user_secret = jwt_auth_config.get("secret")
		
		if not user_secret:
			raise ValueError(f"No JWT secret found for user {username}")
		
		now = datetime.now(timezone.utc)
		payload = {
			"key": username,
			"username": username,
			"iat": int(now.timestamp()),
			"exp": int((now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)).timestamp()),
		}
		
		return jwt.encode(payload, user_secret, algorithm=settings.JWT_ALGORITHM)
	

	def profile_group_exists(self, u_type: str) -> bool:
		"""Check if profile group exists for user type."""
		group = self.consumer_groups.get_consumer_group(u_type)
		return True if group else False