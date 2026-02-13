import requests
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.exceptions import APISIXException


class ConsumerGroupService:
	"""Service for APISIX Consumer Groups management."""
	
	def __init__(self):
		self.admin_url = settings.APISIX_ADMIN_URL
		self.headers = {
			"X-API-KEY": settings.APISIX_ADMIN_KEY,
			"Content-Type": "application/json"
		}
	
	def get_consumer_group(self, group_name: str) -> Optional[Dict[str, Any]]:
		"""Get consumer group from APISIX by name."""
		try:
			url = f"{self.admin_url}/consumer_groups/{group_name}"
			response = requests.get(url, headers=self.headers, timeout=10)
			
			if response.status_code == 200:
				data = response.json()
				return data.get("value")
			elif response.status_code == 404:
				return None
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def create_consumer_group(self, group_name: str, group_config: Dict[str, Any]) -> bool:
		"""Create a new consumer group in APISIX."""
		try:
			url = f"{self.admin_url}/consumer_groups/{group_name}"
			response = requests.put(url, headers=self.headers, json=group_config, timeout=10)
			
			if response.status_code in [200, 201]:
				return True
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def update_consumer_group(self, group_name: str, group_config: Dict[str, Any]) -> bool:
		"""Update an existing consumer group in APISIX."""
		try:
			url = f"{self.admin_url}/consumer_groups/{group_name}"
			response = requests.put(url, headers=self.headers, json=group_config, timeout=10)
			if response.status_code == 200 or response.status_code == 201:
				group = self.get_consumer_group(group_name)
				return True
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def delete_consumer_group(self, group_name: str) -> bool:
		"""Delete a consumer group from APISIX."""
		try:
			url = f"{self.admin_url}/consumer_groups/{group_name}"
			response = requests.delete(url, headers=self.headers, timeout=10)
			
			if response.status_code in [200, 404]:
				return True
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def list_consumer_groups(self) -> List[Dict[str, Any]]:
		"""List all consumer groups from APISIX."""
		try:
			url = f"{self.admin_url}/consumer_groups"
			
			response = requests.get(url, headers=self.headers, timeout=10)
			
			if response.status_code == 200:
				try:
					data = response.json()
					
					# Extract groups from APISIX response format
					groups = []
					if isinstance(data.get("list"), list):
						for item in data["list"]:
							if isinstance(item, dict) and "value" in item:
								group_data = item["value"]
								group_data["id"] = item.get("key", "").split("/")[-1]
								groups.append(group_data)
					return groups
				except ValueError as e:
					raise APISIXException(f"Invalid JSON response: {str(e)}")
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")
	
	def create_profile_group(self, u_type: str, count: int, time_window: int, 
						rejected_code: int, rejected_msg: str, policy: str,
						show_limit_quota_header: bool) -> bool:
		"""Create a consumer group configured as a profile."""
		group_config = {
			"desc": f"Profile group for {u_type} users",
			"plugins": {
				"limit-count": {
					"count": count,
					"time_window": time_window,
					"key": "consumer_name",
					"key_type": "var",
					"rejected_code": rejected_code,
					"rejected_msg": rejected_msg,
					"policy": policy,
					"show_limit_quota_header": show_limit_quota_header,
					"nodelay": False
				}
			}
		}
		
		return self.create_consumer_group(u_type, group_config)
	
	def update_profile_group(self, u_type: str, new_group_name: str, count: int, time_window: int,
						rejected_code: int, rejected_msg: str, policy: str,
						show_limit_quota_header: bool) -> bool:
		"""Update a consumer group configured as a profile."""

		if new_group_name:
			group_name = new_group_name
		else:
			group_name = u_type

		group_config = {
			"desc": f"Profile group for {group_name} users",
			"plugins": {
				"limit-count": {
					"count": count,
					"time_window": time_window,
					"key": "consumer_name", 
					"key_type": "var",
					"rejected_code": rejected_code,
					"rejected_msg": rejected_msg,
					"policy": policy,
					"show_limit_quota_header": show_limit_quota_header,
					"nodelay": False
				}
			}
		}
		
		# If update_consumer_group, exception will be raised
		success = self.update_consumer_group(group_name, group_config)

		# If new_group_name is provided, delete old group
		if new_group_name:
			try:
				self.delete_consumer_group(u_type)
			except APISIXException as e:
				self.delete_consumer_group(new_group_name)
				return False

		return True
	
	def get_profile_groups(self) -> List[Dict[str, Any]]:
		"""Get all consumer groups that function as profiles (have limit-count plugin)."""
		all_groups = self.list_consumer_groups()
		profile_groups = []
		
		for group in all_groups:
			plugins = group.get("plugins", {})
			if "limit-count" in plugins:
				# Transform to profile format
				limit_config = plugins["limit-count"]
				profile_data = {
					"id": group.get("id", "unknown"),
					"u_type": group.get("id", "unknown"),
					"count": limit_config.get("count", 0),
					"time_window": limit_config.get("time_window", 60),
					"rejected_code": limit_config.get("rejected_code", 429),
					"rejected_msg": limit_config.get("rejected_msg", "Rate limit exceeded"),
					"policy": limit_config.get("policy", "local"),
					"show_limit_quota_header": limit_config.get("show_limit_quota_header", True)
				}
				profile_groups.append(profile_data)
		
		return profile_groups
	
	# def assign_consumer_to_group(self, consumer_name: str, group_name: str) -> bool:
	#     """Assign a consumer to a consumer group."""
	#     try:
	#         # Get current consumer config
	#         url = f"{self.admin_url}/apisix/admin/consumers/{consumer_name}"
	#         response = requests.get(url, headers=self.headers, timeout=10)
			
	#         if response.status_code != 200:
	#             raise APISIXException(f"Consumer not found: {response.status_code}")
			
	#         consumer_data = response.json().get("value", {})
			
	#         # Add group assignment
	#         consumer_data["group_id"] = group_name
			
	#         # Update consumer
	#         response = requests.put(url, headers=self.headers, json=consumer_data, timeout=10)
			
	#         if response.status_code == 200:
	#             return True
	#         else:
	#             raise APISIXException(f"Status {response.status_code}: {response.text}")
				
	#     except requests.RequestException as e:
	#         raise APISIXException(f"Connection error: {str(e)}")
	
	# def remove_consumer_from_group(self, consumer_name: str) -> bool:
		"""Remove a consumer from its current group."""
		try:
			# Get current consumer config
			url = f"{self.admin_url}/apisix/admin/consumers/{consumer_name}"
			response = requests.get(url, headers=self.headers, timeout=10)
			
			if response.status_code != 200:
				raise APISIXException(f"Consumer not found: {response.status_code}")
			
			consumer_data = response.json().get("value", {})
			
			# Remove group assignment
			if "group_id" in consumer_data:
				del consumer_data["group_id"]
			
			# Update consumer
			response = requests.put(url, headers=self.headers, json=consumer_data, timeout=10)
			
			if response.status_code == 200:
				return True
			else:
				raise APISIXException(f"Status {response.status_code}: {response.text}")
				
		except requests.RequestException as e:
			raise APISIXException(f"Connection error: {str(e)}")