import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from app.api.deps import (
	get_auth_service,
	get_username_from_apisix_request,
	get_user_service,
	get_login_throttle_service,
)
from app.schemas.auth import UserLogin, Token, FederatedLogin
from app.schemas.user import (
	SendPasswordRecoveryRequest,
	SendPasswordRecoveryResponse,
	PasswordRecoveryRequest,
	PasswordRecoveryResponse,
)
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.login_throttle import LoginThrottleService
from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException, TooManyLoginAttemptsException
import logging
from datetime import datetime

router = APIRouter()

WEB_BASE_URL = os.getenv('WEB_BASE_URL', 'https://zerbitzuak.hitz.eus/nlp_tresnak/')
CRUD_ADMIN = os.getenv('CRUD_ADMIN', 'admin')

@router.post("/token")
async def login(
	request: Request,
	form_data: UserLogin,
	auth_service: AuthService = Depends(get_auth_service),
	throttle_service: LoginThrottleService = Depends(get_login_throttle_service),
):

	def _get_client_ip(req: Request) -> str:
		if settings.TRUST_PROXY:
			fwd = req.headers.get(settings.FORWARDED_FOR_HEADER)
			if fwd:
				# take first IP
				return fwd.split(',')[0].strip()
		return req.client.host

	client_ip = _get_client_ip(request)
	try:
		# Check active lock before processing auth
		locked_until = throttle_service.is_locked(form_data.username, client_ip)
		if locked_until:
			# Calculate retry-after seconds
			retry_after_seconds = max(0, int((locked_until - datetime.now()).total_seconds()))
			return JSONResponse(
				content={"success": False, "access_token": None, "status": None, "http_code": 429},
				headers={"Access-Control-Allow-Credentials": "true", "Retry-After": str(retry_after_seconds)}
			)

		token_data = await auth_service.authenticate_user(form_data)
		if token_data and token_data.access_token:
			# Success: clear any lock and record success
			throttle_service.on_success(form_data.username, client_ip)
			response = JSONResponse(
				content={"success": True, "access_token": token_data.access_token, "status": token_data.status, "http_code": 200},
				headers={"Access-Control-Allow-Credentials": "true"}
			)
		else:
			# Treat as failure
			throttle_service.register_failure_and_lock_if_needed(form_data.username, client_ip)
			response = JSONResponse(
				content={"success": False, "access_token": None, "status": None, "http_code": 401},
				headers={"Access-Control-Allow-Credentials": "true"}
			)
		
		return response
	except InvalidCredentialsException:
		# Invalid credentials: register failure and respond generically
		throttle_service.register_failure_and_lock_if_needed(form_data.username, client_ip)
		return JSONResponse(
			content={"success": False, "access_token": None, "status": None, "http_code": 401},
			headers={"Access-Control-Allow-Credentials": "true"}
		)
	except Exception as e:
		print(e)
		# Generic error
		return JSONResponse(
			content={"success": False, "access_token": None, "status": None, "http_code": 401},
			headers={"Access-Control-Allow-Credentials": "true"}
		)

@router.get("/federated_token", include_in_schema=False)
async def login2(
	request: Request,
	auth_service: AuthService = Depends(get_auth_service)
):
	try:
		headers = request.headers
		
		# data = {
		#     "eppn": headers.get("shib-eppn","ezezaguna"),                       # - "eppn": The user's electronic person principal name.
		#     "mail": headers.get("shib-mail","ezezaguna"),                       # - "mail": The user's email address.
		#     "persistent_id": headers.get("shib-application-id","ezezaguna"),    # - "persistent_id": A unique identifier for the user that persists across sessions.
		#     "sn": headers.get("shib-sn","ezezaguna"),                           # - "sn": The user's surname or last name.
		#     "givenName": headers.get("shib-givenname","ezezaguna"),             # - "givenName": The user's given or first name.
		# }
		
		email = headers.get("shib-mail")
		username, domain = email.split("@")
		username = username.replace(".", "_")
		
		data = {
			"username": username,
			"password": headers.get("shib-session-id","ezezaguna"),
			"email": headers.get("shib-mail","ezezaguna")
		}

		federated_data = FederatedLogin(**data)
		
		token_data = await auth_service.get_federated_token(federated_data)
		response = RedirectResponse(
			url=WEB_BASE_URL,
			status_code=303
		)

		response.set_cookie(
			key="access_token",
			value=token_data["access_token"],
			httponly=True,
			secure=False,
			samesite="lax",
			path="/"
		)
		return response
	except Exception as e:
		print(e)
		return RedirectResponse(
			url=WEB_BASE_URL,
			status_code=303
		)

@router.post("/crud_token", include_in_schema=False)
async def login_crud(
	request: Request,
	form_data: UserLogin,
	auth_service: AuthService = Depends(get_auth_service),
	throttle_service: LoginThrottleService = Depends(get_login_throttle_service),
):

	def _get_client_ip(req: Request) -> str:
		if settings.TRUST_PROXY:
			fwd = req.headers.get(settings.FORWARDED_FOR_HEADER)
			if fwd:
				# take first IP
				return fwd.split(',')[0].strip()
		return req.client.host



	client_ip = _get_client_ip(request)
	try:
		# Check active lock before processing auth
		locked_until = throttle_service.is_locked(form_data.username, client_ip)
		if locked_until:
			# Calculate retry-after seconds
			retry_after_seconds = max(0, int((locked_until - datetime.now()).total_seconds()))
			return JSONResponse(
				content={"success": False, "access_token": None, "http_code": 429},
				headers={"Access-Control-Allow-Credentials": "true", "Retry-After": str(retry_after_seconds)}
			)

		token_data = await auth_service.authenticate_user(form_data)

		#Only admin can login
		if form_data.username != CRUD_ADMIN:
			return JSONResponse(
				content={"success": False, "access_token": None, "http_code": 401},
				headers={"Access-Control-Allow-Credentials": "true"}
			)
		if token_data and token_data.access_token:
			# Success: clear any lock and record success
			throttle_service.on_success(form_data.username, client_ip)
			response = JSONResponse(
				content={"success": True, "access_token": token_data.access_token, "http_code": 200},
				headers={"Access-Control-Allow-Credentials": "true"}
			)
		else:
			# Treat as failure
			throttle_service.register_failure_and_lock_if_needed(form_data.username, client_ip)
			response = JSONResponse(
				content={"success": False, "access_token": None, "http_code": 401},
				headers={"Access-Control-Allow-Credentials": "true"}
			)
		
		return response
	except InvalidCredentialsException:
		# Invalid credentials: register failure and respond generically
		throttle_service.register_failure_and_lock_if_needed(form_data.username, client_ip)
		return JSONResponse(
			content={"success": False, "access_token": None, "http_code": 401},
			headers={"Access-Control-Allow-Credentials": "true"}
		)
	except Exception as e:
		print(e)
		# Generic error
		return JSONResponse(
			content={"success": False, "access_token": None, "http_code": 401},
			headers={"Access-Control-Allow-Credentials": "true"}
		)

@router.get("/check-token")
async def check_token(request: Request):
	token = request.cookies.get('access_token')
	if token:
		return {"success": True, "token": token}
	return {"success": False}


@router.get("/logout", response_model=Token)
async def logout(request: Request):
	try:
		response = RedirectResponse(
			url=WEB_BASE_URL,
			status_code=303
		)

		# Delete all cookies
		for cookie_name in request.cookies.keys():
			response.delete_cookie(key=cookie_name, path="/")
		return response
		
	except Exception as e:
		# Log the error for debugging but don't expose details to user
		logger = logging.getLogger(__name__)
		logger.error(f'Logout error: {str(e)}')
		return RedirectResponse(
			url=WEB_BASE_URL,
			status_code=303
		)

@router.post("/send_pass_recovery", response_model=SendPasswordRecoveryResponse)
async def send_password_recovery(
	payload: SendPasswordRecoveryRequest,
	user_service: UserService = Depends(get_user_service)
) -> SendPasswordRecoveryResponse:
	"""Initiate password recovery flow by sending an email with a reset link.
	Always returns generic success to avoid email enumeration."""
	result = await user_service.send_password_recovery(payload.email)
	return SendPasswordRecoveryResponse(**result)


@router.post("/pass_recovery", response_model=PasswordRecoveryResponse, include_in_schema=False)
async def password_recovery(
	payload: PasswordRecoveryRequest,
	user_service: UserService = Depends(get_user_service)
) -> PasswordRecoveryResponse:
	"""Reset password using a valid token sent via email."""
	result = await user_service.reset_password_with_token(
		code=payload.code,
		new_password=payload.password,
	)
	return PasswordRecoveryResponse(**result)
