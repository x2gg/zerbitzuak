#!/usr/bin/env python3
"""
Standalone Login Test Script
Test APISIX consumer authentication without modifying your main FastAPI app
"""

import requests
import jwt
import json
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration (you can modify these)
JWT_SECRET_KEY = "test-jwt-secret-key-12345"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# APISIX Configuration - MODIFY THESE FOR YOUR SETUP
APISIX_ADMIN_URL = "http://localhost:9180"  # Change to your APISIX admin URL
APISIX_ADMIN_KEY = "edd1c9f034335f136f87ad84b625c8f1"  # Change to your admin key

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginTester:
	def __init__(self):
		self.headers = {
			"X-API-KEY": APISIX_ADMIN_KEY,
			"Content-Type": "application/json"
		}
	
	def get_consumer_by_username(self, username: str) -> Optional[Dict]:
		"""Fetch consumer from APISIX by username"""
		try:
			url = f"{APISIX_ADMIN_URL}/apisix/admin/consumers/{username}"
			response = requests.get(url, headers=self.headers, timeout=10)
			
			if response.status_code == 200:
				data = response.json()
				return data.get("value")
			elif response.status_code == 404:
				logger.warning(f"Consumer '{username}' not found")
				return None
			else:
				logger.error(f"APISIX API error: {response.status_code} - {response.text}")
				return None
				
		except requests.RequestException as e:
			logger.error(f"Error connecting to APISIX: {e}")
			return None
	
	def verify_basic_auth_credentials(self, consumer_data: Dict, password: str) -> bool:
		"""Verify password against basic-auth plugin"""
		plugins = consumer_data.get("plugins", {})
		basic_auth = plugins.get("basic-auth")
		
		if not basic_auth:
			logger.info("Consumer doesn't have basic-auth plugin configured")
			return False
		
		stored_password = basic_auth.get("password")
		if not stored_password:
			logger.warning("No password found in basic-auth plugin")
			return False
		
		# Check if password is hashed (bcrypt starts with $2b$)
		if stored_password.startswith("$2b$"):
			result = pwd_context.verify(password, stored_password)
			logger.info(f"Bcrypt password verification: {'SUCCESS' if result else 'FAILED'}")
			return result
		else:
			# Plain text comparison
			result = password == stored_password
			logger.info(f"Plain text password verification: {'SUCCESS' if result else 'FAILED'}")
			return result
	
	def verify_jwt_auth_credentials(self, consumer_data: Dict, password: str) -> bool:
		"""Verify password against jwt-auth plugin"""
		plugins = consumer_data.get("plugins", {})
		jwt_auth = plugins.get("jwt-auth")
		
		if not jwt_auth:
			logger.info("Consumer doesn't have jwt-auth plugin configured")
			return False
		
		stored_secret = jwt_auth.get("secret") or jwt_auth.get("password")
		if not stored_secret:
			logger.warning("No secret/password found in jwt-auth plugin")
			return False
		
		if stored_secret.startswith("$2b$"):
			result = pwd_context.verify(password, stored_secret)
			logger.info(f"JWT-auth bcrypt verification: {'SUCCESS' if result else 'FAILED'}")
			return result
		else:
			result = password == stored_secret
			logger.info(f"JWT-auth plain text verification: {'SUCCESS' if result else 'FAILED'}")
			return result
	
	def create_jwt_token(self, username: str, consumer_data: Dict) -> str:
		"""Create JWT token"""
		plugins = consumer_data.get("plugins", {})
		
		payload = {
			"sub": username,
			"username": username,
			"iat": datetime.utcnow(),
			"exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
			"consumer_id": consumer_data.get("username", username),
		}
		
		# Add auth type information
		if "basic-auth" in plugins:
			payload["auth_type"] = "basic-auth"
		if "jwt-auth" in plugins:
			payload["auth_type"] = "jwt-auth"
		
		# Add description if available
		desc = consumer_data.get("desc", "")
		if desc:
			payload["description"] = desc
		
		return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
	
	def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
		"""Main authentication function"""
		logger.info(f"=== Attempting to authenticate user: {username} ===")
		
		# Get consumer from APISIX
		consumer_data = self.get_consumer_by_username(username)
		
		if not consumer_data:
			return {"success": False, "error": "Consumer not found"}
		
		logger.info(f"Consumer found: {consumer_data.get('username')}")
		logger.info(f"Available plugins: {list(consumer_data.get('plugins', {}).keys())}")
		
		# Check if consumer is disabled
		if consumer_data.get("status") == 0:
			return {"success": False, "error": "Consumer is disabled"}
		
		# Try authentication
		is_authenticated = False
		auth_method = None
		
		# Try basic-auth first
		if self.verify_basic_auth_credentials(consumer_data, password):
			is_authenticated = True
			auth_method = "basic-auth"
		
		# Try jwt-auth if basic-auth failed
		elif self.verify_jwt_auth_credentials(consumer_data, password):
			is_authenticated = True
			auth_method = "jwt-auth"
		
		if not is_authenticated:
			return {"success": False, "error": "Invalid credentials"}
		
		# Create JWT token
		access_token = self.create_jwt_token(username, consumer_data)
		
		return {
			"success": True,
			"access_token": access_token,
			"token_type": "bearer",
			"expires_in": JWT_EXPIRATION_HOURS * 3600,
			"auth_method": auth_method,
			"user_info": {
				"username": username,
				"consumer_id": consumer_data.get("username", username),
				"plugins": list(consumer_data.get("plugins", {}).keys()),
				"description": consumer_data.get("desc", "")
			}
		}
	
	def verify_jwt_token(self, token: str) -> Dict[str, Any]:
		"""Verify JWT token"""
		try:
			payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
			return {"valid": True, "payload": payload}
		except jwt.ExpiredSignatureError:
			return {"valid": False, "error": "Token has expired"}
		except jwt.JWTError as e:
			return {"valid": False, "error": f"Invalid token: {str(e)}"}
	
	def create_test_consumer(self, username: str, password: str, auth_type: str = "basic-auth"):
		"""Create a test consumer in APISIX"""
		logger.info(f"=== Creating test consumer: {username} with {auth_type} ===")
		
		hashed_password = pwd_context.hash(password)
		
		consumer_data = {
			"username": username,
			"desc": f"Test consumer created by script - {auth_type}",
			"plugins": {}
		}
		
		if auth_type == "basic-auth":
			consumer_data["plugins"]["basic-auth"] = {
				"username": username,
				"password": hashed_password
			}
		elif auth_type == "jwt-auth":
			consumer_data["plugins"]["jwt-auth"] = {
				"key": username,
				"secret": hashed_password,
				"algorithm": "HS256"
			}
		
		try:
			url = f"{APISIX_ADMIN_URL}/apisix/admin/consumers/{username}"
			response = requests.put(url, json=consumer_data, headers=self.headers, timeout=10)
			
			if response.status_code in [200, 201]:
				logger.info(f"✅ Consumer '{username}' created successfully")
				return True
			else:
				logger.error(f"❌ Failed to create consumer: {response.status_code} - {response.text}")
				return False
				
		except requests.RequestException as e:
			logger.error(f"❌ Error creating consumer: {e}")
			return False
	
	def delete_test_consumer(self, username: str):
		"""Delete a test consumer from APISIX"""
		try:
			url = f"{APISIX_ADMIN_URL}/apisix/admin/consumers/{username}"
			response = requests.delete(url, headers=self.headers, timeout=10)
			
			if response.status_code in [200, 404]:  # 404 is ok, means already deleted
				logger.info(f"✅ Consumer '{username}' deleted")
				return True
			else:
				logger.error(f"❌ Failed to delete consumer: {response.status_code}")
				return False
		except requests.RequestException as e:
			logger.error(f"❌ Error deleting consumer: {e}")
			return False


def main():
	"""Main test function"""
	print("🚀 APISIX Consumer Authentication Tester")
	print("=" * 50)
	
	tester = LoginTester()
	
	# Test credentials
	test_username = "testuser"
	test_password = "testpass123"
	
	print(f"\n📋 Configuration:")
	print(f"   APISIX Admin URL: {APISIX_ADMIN_URL}")
	print(f"   JWT Secret: {JWT_SECRET_KEY[:10]}...")
	print(f"   Test User: {test_username}")
	
	# Menu
	while True:
		print(f"\n🔧 Available actions:")
		print("1. Create test consumer (basic-auth)")
		print("2. Create test consumer (jwt-auth)")
		print("3. Test login")
		print("4. Verify JWT token")
		print("5. Delete test consumer")
		print("6. List consumer info")
		print("0. Exit")
		
		choice = input("\nSelect option (0-6): ").strip()
		
		if choice == "1":
			tester.create_test_consumer(test_username, test_password, "basic-auth")
			
		elif choice == "2":
			tester.create_test_consumer(test_username, test_password, "jwt-auth")
			
		elif choice == "3":
			username = input(f"Username ({test_username}): ").strip() or test_username
			password = input(f"Password ({test_password}): ").strip() or test_password
			
			result = tester.authenticate_user(username, password)
			
			if result["success"]:
				print(f"\n✅ Authentication SUCCESS!")
				print(f"   Auth method: {result['auth_method']}")
				print(f"   Token type: {result['token_type']}")
				print(f"   Expires in: {result['expires_in']} seconds")
				print(f"   User info: {json.dumps(result['user_info'], indent=2)}")
				print(f"\n🎫 JWT Token:")
				print(f"   {result['access_token'][:50]}...")
			else:
				print(f"\n❌ Authentication FAILED: {result['error']}")
		
		elif choice == "4":
			token = input("Enter JWT token to verify: ").strip()
			result = tester.verify_jwt_token(token)
			
			if result["valid"]:
				print(f"\n✅ Token is VALID")
				print(f"   Payload: {json.dumps(result['payload'], indent=2, default=str)}")
			else:
				print(f"\n❌ Token is INVALID: {result['error']}")
		
		elif choice == "5":
			username = input(f"Username to delete ({test_username}): ").strip() or test_username
			tester.delete_test_consumer(username)
		
		elif choice == "6":
			username = input(f"Username to check ({test_username}): ").strip() or test_username
			consumer = tester.get_consumer_by_username(username)
			
			if consumer:
				print(f"\n📋 Consumer info for '{username}':")
				print(json.dumps(consumer, indent=2))
			else:
				print(f"\n❌ Consumer '{username}' not found")
		
		elif choice == "0":
			print("\n👋 Goodbye!")
			break
		
		else:
			print("❌ Invalid option")


if __name__ == "__main__":
	# Check if required packages are installed
	try:
		import requests
		import jwt
		from passlib.context import CryptContext
	except ImportError as e:
		print(f"❌ Missing required package: {e}")
		print("Install with: pip install requests PyJWT passlib[bcrypt]")
		exit(1)
	
	main()