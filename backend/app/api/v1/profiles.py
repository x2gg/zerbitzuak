from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.api.deps import get_profile_service
from app.schemas.profile import Profile, ProfileCreate, ProfileUpdate
from app.services.profile import ProfileService
from app.core.exceptions import ProfileAlreadyExistsException
from app.core.security import ensure_admin_request

router = APIRouter()

@router.post("/", response_model=Profile, include_in_schema=False)
async def create_profile(
	request: Request,
	profile: ProfileCreate,
	profile_service: ProfileService = Depends(get_profile_service)
) -> Profile:
	"""Create a new profile."""

	ensure_admin_request(request)

	return await profile_service.create_profile(profile)

@router.post("/sync-defaults", include_in_schema=False)
async def sync_default_profiles(
	request: Request,
	profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
	"""Sync default profiles (basic and pro) with APISIX."""

	ensure_admin_request(request)
	
	created = []
	errors = []
	
	default_profiles = [
		ProfileCreate(
			u_type="basic",
			count=settings.BASIC_USER_COUNT,
			time_window=60,
			rejected_code=429,
			rejected_msg=settings.BASIC_USER_MSG,
			policy="local",
			show_limit_quota_header=True
		),
		ProfileCreate(
			u_type="pro",
			count=settings.PRO_USER_COUNT,
			time_window=60,
			rejected_code=429,
			rejected_msg=settings.PRO_USER_MSG,
			policy="local",
			show_limit_quota_header=True
		)
	]
	
	for profile_data in default_profiles:
		try:
			await profile_service.create_profile(profile_data)
			created.append(profile_data.u_type)
		except ProfileAlreadyExistsException:
			# Update existing profile instead
			try:
				profile = await profile_service.get_profile(profile_data.u_type)
				await profile_service.update_profile(
					profile.id, 
					ProfileUpdate(**profile_data.dict())
				)
				created.append(f"{profile_data.u_type} (updated)")
			except Exception as e:
				errors.append(f"{profile_data.u_type}: {str(e)}")
		except Exception as e:
			errors.append(f"{profile_data.u_type}: {str(e)}")
	
	return {
		"created": created,
		"errors": errors
	}

@router.get("/{profile_id}", response_model=Profile, include_in_schema=False)
async def read_profile(
	request: Request,
	profile_id: str,
	profile_service: ProfileService = Depends(get_profile_service)
) -> Profile:
	"""Get a specific profile by ID."""

	ensure_admin_request(request)
	
	return await profile_service.get_profile(profile_id)


@router.put("/{profile_id}", response_model=Profile, include_in_schema=False)
async def update_profile(
	request: Request,
	profile_id: str,
	profile: ProfileUpdate,
	profile_service: ProfileService = Depends(get_profile_service)
) -> Profile:
	"""Update a profile."""

	ensure_admin_request(request)

	return await profile_service.update_profile(profile_id, profile)


@router.delete("/{profile_id}", include_in_schema=False)
async def delete_profile(
	request: Request,
	profile_id: str,
	profile_service: ProfileService = Depends(get_profile_service)
) -> dict:
	"""Delete a profile."""

	ensure_admin_request(request)

	return await profile_service.delete_profile(profile_id)


@router.get("/", response_model=List[Profile], include_in_schema=False)
async def list_profiles(
	request: Request,
	profile_service: ProfileService = Depends(get_profile_service)
) -> List[Profile]:
	"""List all profiles."""

	ensure_admin_request(request)

	try:
		return await profile_service.list_profiles()
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Error listing profiles: " + str(e)
		)