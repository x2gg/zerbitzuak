from typing import List, Dict, Any

from app.services.consumer_group import ConsumerGroupService
from app.schemas.profile import Profile, ProfileCreate, ProfileUpdate
from app.core.exceptions import ProfileNotFoundException, ProfileAlreadyExistsException, DatabaseException


class ProfileService:
	"""Service for profile management operations."""
	
	def __init__(self, profile_repository=None):
		self.consumer_group_service = ConsumerGroupService()
	
	async def create_profile(self, profile_data: ProfileCreate) -> Profile:
		"""Create a new profile using Consumer Groups."""
		# Check if profile group already exists
		existing_group = self.consumer_group_service.get_consumer_group(profile_data.u_type)
		if existing_group:
			# Check if it's a profile group (has limit-count plugin)
			if "limit-count" in existing_group.get("plugins", {}):
				raise ProfileAlreadyExistsException(profile_data.u_type)
			else:
				# It's a regular consumer group, we can convert it to a profile
				logger.warning(f"Converting existing consumer group '{profile_data.u_type}' to profile")
		
		try:
			# Create consumer group
			success = self.consumer_group_service.create_profile_group(
				u_type=profile_data.u_type,
				count=profile_data.count,
				time_window=profile_data.time_window,
				rejected_code=profile_data.rejected_code,
				rejected_msg=profile_data.rejected_msg,
				policy=profile_data.policy,
				show_limit_quota_header=profile_data.show_limit_quota_header
			)
			
			if not success:
				raise DatabaseException("Failed to create consumer group")
			
			# Return created profile
			created_group = self.consumer_group_service.get_consumer_group(profile_data.u_type)
			if not created_group:
				raise DatabaseException("Failed to retrieve created group")
			
			# Transform group to profile format
			limit_config = created_group.get("plugins", {}).get("limit-count", {})
			profile = Profile(
				id=profile_data.u_type,  # Use u_type as ID for groups
				u_type=profile_data.u_type,
				count=limit_config.get("count", profile_data.count),
				time_window=limit_config.get("time_window", profile_data.time_window),
				rejected_code=limit_config.get("rejected_code", profile_data.rejected_code),
				rejected_msg=limit_config.get("rejected_msg", profile_data.rejected_msg),
				policy=limit_config.get("policy", profile_data.policy),
				show_limit_quota_header=limit_config.get("show_limit_quota_header", profile_data.show_limit_quota_header)
			)
			
			return profile
			
		except Exception as e:
			raise e
	
	async def get_profile(self, profile_id: str) -> Profile:
		"""Get a profile by ID (u_type)."""
		# Convert ID to string for group lookup
		u_type = profile_id
		
		group = self.consumer_group_service.get_consumer_group(u_type)
		if not group:
			raise ProfileNotFoundException(profile_id)
		
		# Check if it has limit-count plugin (is a profile group)
		plugins = group.get("plugins", {})
		if "limit-count" not in plugins:
			raise ProfileNotFoundException(profile_id)
		
		limit_config = plugins["limit-count"]
		return Profile(
			id=u_type,
			u_type=u_type,
			count=limit_config.get("count", 0),
			time_window=limit_config.get("time_window", 60),
			rejected_code=limit_config.get("rejected_code", 429),
			rejected_msg=limit_config.get("rejected_msg", "Rate limit exceeded"),
			policy=limit_config.get("policy", "local"),
			show_limit_quota_header=limit_config.get("show_limit_quota_header", True)
		)
	
	async def update_profile(self, profile_id: str, profile_update: ProfileUpdate) -> Profile:
		"""Update a profile."""
		u_type = profile_id
		
		# Get existing group
		existing_group = self.consumer_group_service.get_consumer_group(u_type)
		if not existing_group:
			raise ProfileNotFoundException(profile_id)
		
		# Get current config
		current_limit = existing_group.get("plugins", {}).get("limit-count", {})
		
		try:
			# Update group with new values or keep current ones if not provided
			update_data = profile_update.dict(exclude_unset=True)
			
			# If no fields to update, return current profile
			if not update_data:
				return await self.get_profile(profile_id)
			
			# Update group with new values or keep current ones if not provided
			count = update_data.get("count", current_limit.get("count", 0))
			time_window = update_data.get("time_window", current_limit.get("time_window", 60))
			rejected_code = update_data.get("rejected_code", current_limit.get("rejected_code", 429))
			rejected_msg = update_data.get("rejected_msg", current_limit.get("rejected_msg", "Rate limit exceeded"))
			policy = update_data.get("policy", current_limit.get("policy", "local"))
			show_limit_quota_header = update_data.get("show_limit_quota_header", 
										   current_limit.get("show_limit_quota_header", True))
			if update_data.get("u_type", u_type) != u_type:
				new_u_type = update_data.get("u_type", u_type)
			else:
				new_u_type = None

			# Update group
			success = self.consumer_group_service.update_profile_group(
				u_type=u_type,
				new_group_name=new_u_type,
				count=count,
				time_window=time_window,
				rejected_code=rejected_code,
				rejected_msg=rejected_msg,
				policy=policy,
				show_limit_quota_header=show_limit_quota_header
			)
			if not success:
				raise DatabaseException("Failed to update consumer group")
			
			# Return updated profile
			return await self.get_profile(profile_id if not new_u_type else new_u_type)
			
		except Exception as e:
			raise e
	
	async def delete_profile(self, profile_id: str) -> Dict[str, str]:
		"""Delete a profile."""
		u_type = profile_id
		
		# Check if group exists
		group = self.consumer_group_service.get_consumer_group(u_type)
		if not group:
			raise ProfileNotFoundException(profile_id)
		
		try:
			# Delete consumer group
			success = self.consumer_group_service.delete_consumer_group(u_type)
			
			if not success:
				raise DatabaseException("Failed to delete consumer group")
			
			return {"message": f"Profile {profile_id} deleted"}
			
		except Exception as e:
			raise e
	
	async def list_profiles(self) -> List[Profile]:
		"""List all profiles."""
		profile_groups = self.consumer_group_service.get_profile_groups()
		
		profiles = []
		for group_data in profile_groups:
			profile = Profile(**group_data)
			profiles.append(profile)
		
		return profiles