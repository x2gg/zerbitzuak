from typing import Optional, List, Dict, Any
from app.repositories.base import BaseRepository
from app.schemas.profile import Profile
from app.services.consumer_group import ConsumerGroupService


class ProfileRepository(BaseRepository[Profile]):
	"""
	Wrapper repository for profile operations using Consumer Groups.
	Maintains compatibility with existing interface while working with APISIX.
	"""
	
	def __init__(self, connection=None):
		# Don't call super().__init__ as we don't need database connection
		self.consumer_group_service = ConsumerGroupService()
	
	@property
	def table_name(self) -> str:
		return "consumer_groups"  # Conceptual table name
	
	def get_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
		"""Get a profile by ID (u_type)."""
		u_type = profile_id
		if not u_type:
			return None
		group = self.consumer_group_service.get_consumer_group(u_type)
		
		if not group:
			return None
		
		# Check if it has limit-count plugin (is a profile group)
		plugins = group.get("plugins", {})
		if "limit-count" not in plugins:
			return None
		
		limit_config = plugins["limit-count"]
		return {
			"id": u_type,
			"u_type": u_type,
			"count": limit_config.get("count", 0),
			"time_window": limit_config.get("time_window", 60),
			"rejected_code": limit_config.get("rejected_code", 429),
			"rejected_msg": limit_config.get("rejected_msg", "Rate limit exceeded"),
			"policy": limit_config.get("policy", "local"),
			"show_limit_quota_header": limit_config.get("show_limit_quota_header", True)
		}
	
	def get_by_u_type(self, u_type: str) -> Optional[Dict[str, Any]]:
		"""Get a profile by user type."""
		return self.get_by_id(u_type)
	
	def get_all(self) -> List[Dict[str, Any]]:
		"""Get all profiles."""
		return self.consumer_group_service.get_profile_groups()
	
	def create(self, profile_data: Dict[str, Any]) -> str:
		"""Create a new profile and return the ID (u_type)."""
		success = self.consumer_group_service.create_profile_group(
			u_type=profile_data["u_type"],
			count=profile_data["count"],
			time_window=profile_data["time_window"],
			rejected_code=profile_data["rejected_code"],
			rejected_msg=profile_data["rejected_msg"],
			policy=profile_data["policy"],
			show_limit_quota_header=profile_data["show_limit_quota_header"]
		)
		
		if success:
			return profile_data["u_type"]
		else:
			raise Exception("Failed to create consumer group")
	
	def update(self, profile_id: str, profile_data: Dict[str, Any]) -> bool:
		"""Update a profile."""
		if not profile_data:
			return False
		
		u_type = profile_id
		
		# Get current config to merge with updates
		current = self.get_by_id(profile_id)
		if not current:
			return False
		
		# Merge current config with updates
		merged_data = current.copy()
		merged_data.update({k: v for k, v in profile_data.items() if v is not None})
		
		return self.consumer_group_service.update_profile_group(
			u_type=u_type,
			count=merged_data["count"],
			time_window=merged_data["time_window"],
			rejected_code=merged_data["rejected_code"],
			rejected_msg=merged_data["rejected_msg"],
			policy=merged_data["policy"],
			show_limit_quota_header=merged_data["show_limit_quota_header"]
		)
	
	def delete(self, profile_id: str) -> bool:
		"""Delete a profile."""
		u_type = profile_id
		return self.consumer_group_service.delete_consumer_group(u_type)
	
	# Override base methods to avoid database operations
	def commit(self) -> None:
		"""No-op for Consumer Groups."""
		pass
	
	def rollback(self) -> None:
		"""No-op for Consumer Groups."""
		pass
	
	def close(self) -> None:
		"""No-op for Consumer Groups."""
		pass