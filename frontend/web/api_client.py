"""API client helpers for interacting with the FastAPI backend exposed through APISIX.
All HTTP logic is isolated here so that the rest of the frontend remains
clean and testable.
"""
from __future__ import annotations

import os
import requests
from typing import Any, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APISIX_URL: str = os.getenv("APISIX_URL", "https://dev.hitz.eus/api")
GUEST_NLP_TIMEOUT = int(os.getenv("GUEST_NLP_TIMEOUT", 10))
NLP_TIMEOUT = int(os.getenv("NLP_TIMEOUT", 30))

# APISIX_URL = "https://dev.hitz.eus/admin/"

DEFAULT_HEADERS = {
	"Content-Type": "application/json",
}

session = requests.Session()

# ---------------------------------------------------------------------------
# High-level request helpers
# ---------------------------------------------------------------------------


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
	"""Login against the `/token` endpoint.

	Returns
	-------
	success : bool
	username : str | None
	token : str | None
	status : str | None
	"""
	try:
		response = session.post(
			f"{APISIX_URL}/login",
			headers=DEFAULT_HEADERS,
			json={"username": username, "password": password},
			timeout=10,
		)
		retry_after = response.headers.get("Retry-After")
		if retry_after:
			retry_after = int(retry_after)

		data = response.json()
		if data.get("http_code") == 200 and data.get("access_token"):
			return True, username, data.get("access_token"), data.get("status")
		elif data.get("http_code") == 429:
			return False, None, None, "429"
		return False, None, None, None
	except Exception:
		# Silent fail – caller decides message
		return False, None, None, None


# def logout(token):
#     try:
#         response = session.get(
#             f"{APISIX_URL}/logout",
#             headers={"Authorization": f"Bearer {token}"},
#             timeout=10,
#         )
#         return response.status_code == 200
#     except Exception as e:
#         return f"Error al cerrar sesión: {str(e)}"

def register_user(
	username: str, email: str, password: str
) -> Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[str], Optional[int], Optional[int]]:
	"""Register and optionally log in a user.

	Returns
	-------
	success, username, token, status, error_msg, count, http_code
	"""
	try:
		response = session.post(
			f"{APISIX_URL}/register",
			headers=DEFAULT_HEADERS,
			json={"username": username, "email": email, "password": password},
			timeout=10,
		)

		# Raise exception if response is not 2xx
		response.raise_for_status()

		# Registration OK ‑> login to get token
		success, user, token, status = authenticate_user(username, password)
		if success:
			return True, user, token, status, None, None, None
		return True, username, None, None, None, None, None
	except requests.exceptions.HTTPError as e:
		if e.response.status_code == 400:
			error_data = e.response.json()
			msg = error_data.get("detail")
			if msg:
				error_msg, count = msg.split(';')
				return False, None, None, None, error_msg, int(count), e.response.status_code
			return False, None, None, None, None, None, e.response.status_code
		else:
			raise
	except Exception as exc:
		return False, None, None, None, None, None, None


def send_verification_code(token: str) -> Tuple[bool, str, Optional[str]]:
	"""Trigger email verification code sending."""
	try:
		resp = requests.get(
			f"{APISIX_URL}/users/send-verification",
			headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {token}"},
			timeout=10,
		)
		data = resp.json()
		return data.get("success", False), data.get("message", ""), data.get("email")
	except Exception as exc:
		return False, f"Error: {exc}", None


def get_profile(token: str) -> Tuple[bool, Dict[str, Any] | None, str]:
	"""Fetch user profile data."""
	try:
		resp = requests.get(
			f"{APISIX_URL}/users/profile",
			headers={"Authorization": f"Bearer {token}"},
			timeout=10,
		)
		if resp.status_code == 200:
			return True, resp.json()
		return False, None
	except Exception as exc:
		return False, None


def verify_email(token: str, code: str) -> Tuple[bool, str, bool]:
	"""Verify email with code."""
	try:
		resp = requests.post(
			f"{APISIX_URL}/users/verify-email",
			headers={"Authorization": f"Bearer {token}", **DEFAULT_HEADERS},
			json={"code": code},
			timeout=10,
		)
		if resp.status_code == 200:
			data = resp.json()
			return True, data.get("verified", False)
		return False, False
	except Exception as exc:
		return False, False

# ---------------------------------------------------------------------------
# Password reset helpers
# ---------------------------------------------------------------------------

def request_password_reset(email: str) -> tuple[bool, str]:
	"""Request a password reset code to be sent to the user's email.

	Returns
	-------
	success : bool
	message : str
		Success or error message returned by the backend.
	"""
	try:
		resp = requests.post(
			f"{APISIX_URL}/send_pass_recovery",
			headers=DEFAULT_HEADERS,
			json={"email": email},
			timeout=10,
		)
		data = resp.json()
		if resp.status_code == 200 and data.get("success", False):
			return True, data.get("message", "Password reset code sent")
		return False, ""
	except Exception as exc:
		return False, ""


def reset_password(code: str, new_password: str) -> tuple[bool, str]:
	"""Complete password reset with verification code and new password."""
	try:
		resp = requests.post(
			f"{APISIX_URL}/pass_recovery",
			headers=DEFAULT_HEADERS,
			json={"code": code, "password": new_password},
			timeout=10,
		)
		data = resp.json()
		if resp.status_code == 200 and data.get("success", False):
			return True, data.get("message", "Password reset successful")
		return False, ""
	except Exception as exc:
		return False, ""

# ---------------------------------------------------------------------------
# API key helper
# ---------------------------------------------------------------------------

def generate_api_key(token: str) -> Tuple[bool, Dict[str, Any] | None, str]:
	"""Generate a new API key for the authenticated user.

	Returns
	-------
	success : bool
	data : dict | None
		Full JSON response from backend when success is True
	error_msg : str
		Error description when success is False
	"""
	try:
		resp = requests.get(
			f"{APISIX_URL}/api_key",
			headers={"Authorization": f"Bearer {token}", **DEFAULT_HEADERS},
			timeout=10,
		)
		data = resp.json()
		if resp.status_code == 200 and data.get("success"):
			return True, data
		# fallback error message
		return False, None
	except Exception as exc:
		return False, None

# ---------------------------------------------------------------------------
# NLP endpoints helpers
# ---------------------------------------------------------------------------

def post_lemmatizer(text: str, headers: Dict[str, str]) -> requests.Response:
	return requests.post(f"{APISIX_URL}/lemma", headers=headers, json={"text": text}, timeout=NLP_TIMEOUT)


def post_lemmatizer_guest(text: str, headers: Dict[str, str]) -> requests.Response:
	return requests.post(f"{APISIX_URL}/lemma_guest", headers=headers, json={"text": text}, timeout=GUEST_NLP_TIMEOUT)


def post_nerc(text: str, headers: Dict[str, str]) -> requests.Response:
	return requests.post(f"{APISIX_URL}/nerc", headers=headers, json={"text": text}, timeout=NLP_TIMEOUT)


def post_nerc_guest(text: str, headers: Dict[str, str]) -> requests.Response:
	return requests.post(f"{APISIX_URL}/nerc_guest", headers=headers, json={"text": text}, timeout=GUEST_NLP_TIMEOUT)


def post_nerc_file(file_path: str, headers: Dict[str, str]) -> requests.Response:
	with open(file_path, 'rb') as f:
		files = {'file': (os.path.basename(file_path), f, 'text/plain')}
		return requests.post(
			f"{APISIX_URL}/nerc_file",
			headers={
				"Authorization": headers.get("Authorization")
				# "Content-Type": "multipart/form-data"
			},
			files=files,
			timeout=NLP_TIMEOUT
		)


def post_lemmatizer_file(file_path: str, headers: Dict[str, str]) -> requests.Response:
	with open(file_path, 'rb') as f:
		files = {'file': (os.path.basename(file_path), f, 'text/plain')}
		return requests.post(
			f"{APISIX_URL}/lemma_file",
			headers={
				"Authorization": headers.get("Authorization")
				# "Content-Type": "multipart/form-data"
			},
			files=files,
			timeout=NLP_TIMEOUT
		)
