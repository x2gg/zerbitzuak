"""Gradio callback handlers.

All callbacks are pure functions receiving Gradio component values and returning
Gradio updates. They rely on `api_client` for network calls and `formatters`
for HTML generation.
"""
from __future__ import annotations

from utils.file_processor import file_processor

import gradio as gr
from typing import Any, Dict, Tuple
import os
import tempfile, json

import api_client as api
import formatters
import i18n


def load_css_safe(file_path):
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			return f.read()
	except FileNotFoundError:
		return ""

# Backward-compatible translation function
def t(key: str, **kwargs) -> str:
	return i18n.t(key, **kwargs)

# Language helpers re-exported for UI
def set_language(language: str) -> None:
	i18n.set_language(language)

def get_current_language() -> str:
	return i18n.get_current_language()

def get_available_languages() -> list[str]:
	return i18n.get_available_languages()

USERNAME_MIN_LENGTH = os.getenv("USERNAME_MIN_LENGTH", 3)
USERNAME_MAX_LENGTH = os.getenv("USERNAME_MAX_LENGTH", 64)
PASSWORD_MIN_LENGTH = os.getenv("PASSWORD_MIN_LENGTH", 8)
PASSWORD_MAX_LENGTH = os.getenv("PASSWORD_MAX_LENGTH", 64)

# ----------------------------------------------------------------------------
# Centralized modal navigation helpers
# ----------------------------------------------------------------------------

def navigate_to_modal(target_modal: str | None, nav_state_value: dict, close_tabs: bool = True):
	"""Navigate to a target modal, hiding all others and optionally keeping tabs visible.

	Parameters
	----------
	target_modal : str | None
		Identifier of the modal to show ("login", "profile", "email_verification", "password_reset", "api_key")
		or None to hide all modals.
	nav_state_value : dict
		Current navigation state with keys ``current_modal`` and ``previous_modal``.
	close_tabs : bool, default True
		If True, the main tabs will be hidden whenever a modal is opened. When ``target_modal`` is None
		and ``close_tabs`` is False, the tabs remain visible - useful for Cancel buttons that simply close
		the current modal.

	Returns
	-------
	list
		First element is the updated nav_state dict followed by ``gr.update`` objects for:
		login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, tabs
	"""
	new_nav_state = {
		"current_modal": target_modal,
		"previous_modal": nav_state_value.get("current_modal")
	}

	def _visible(mod_name: str):
		return target_modal == mod_name

	return [
		new_nav_state,
		gr.update(visible=_visible("login")),
		gr.update(visible=_visible("profile")),
		gr.update(visible=_visible("email_verification")),
		gr.update(visible=_visible("password_request")),
		gr.update(visible=_visible("password_reset")),
		gr.update(visible=_visible("api_key")),
		gr.update(visible=(target_modal is None and not close_tabs))
	]


def go_back(nav_state_value: dict):
	"""Return to the previous modal stored in nav_state_value."""
	return navigate_to_modal(nav_state_value.get("previous_modal"), nav_state_value)


def validate_navigation(current_modal: str | None, auth_state: dict) -> bool:
	"""Validate whether the target modal is allowed given the authentication state."""
	if current_modal in ["profile", "api_key"] and not auth_state.get("authenticated"):
		return False
	return True

# ----------------------------------------------------------------------------
# Utility helpers
# ----------------------------------------------------------------------------

def show_login_modal() -> list[Any]:
	"""Return gr.update list to display login modal."""
	return [
		gr.update(value=""),  # modal_title
		gr.update(value=""),  # email_input
		gr.update(value=""),  # password_input
		gr.update(value=""),  # password_confirm_input
		gr.update(visible=True),  # login_modal
		gr.update(visible=False),  # tabs
	]


def hide_login_modal() -> list[Any]:
	"""Hide login modal and reset mode."""
	return [
		gr.update(visible=False),  # login_modal
		gr.update(value=""),  # username_input
		gr.update(value=""),  # password_input
		gr.update(value=""),  # email_input
		gr.update(value=""),  # password_confirm_input
		gr.update(value=""),  # login_message
		False,  # is_register_mode reset
		gr.update(visible=True),  # tabs
	]


def update_header_auth_state(authenticated: bool, username: str | None = None) -> list[gr.update]:
	if authenticated:
		return [
			gr.update(visible=False),       # login_btn
			gr.update(visible=False),       # federated_login_btn
			gr.update(visible=True),        # profile_btn
			gr.update(visible=True, value=f"👤 ✅ **{username}**"),  # user_info
			gr.update(visible=True),        # logout_btn
		]
	return [
		gr.update(visible=True),    # login_btn
		gr.update(visible=True),    # federated_login_btn
		gr.update(visible=False),   # profile_btn
		gr.update(visible=False),   # user_info
		gr.update(visible=False),   # logout_btn
	]


def toggle_register_mode(is_register: bool) -> list[Any]:
	if is_register:
		# Switch to login mode
		return [
			False,                                      # is_register_mode
			gr.update(value=t('authentication.login_modal_title')),  # modal_title
			gr.update(value="", visible=False),         # email_input
			gr.update(value="", visible=False),         # password_confirm_input
			gr.update(value=t('authentication.login_button')),  # modal_login_btn
			gr.update(value=t('authentication.switch_to_register')),  # switch_mode_btn
			gr.update(value=""),                        # login_message
			gr.update(value=""),                        # username_input
			gr.update(value=""),                        # password_input
			gr.update(visible=True),                    # forgotten_password_btn
		]
	# Switch to register mode
	return [
		True,                                           # is_register_mode
		gr.update(value=t('authentication.register_modal_title')),  # modal_title
		gr.update(value="", visible=True),              # email_input
		gr.update(value="", visible=True),              # password_confirm_input
		gr.update(value=t('authentication.register_button')),  # modal_login_btn
		gr.update(value=t('authentication.switch_to_login')),  # switch_mode_btn
		gr.update(value=""),                            # login_message
		gr.update(value=""),                            # clear username field
		gr.update(value=""),                            # clear password field
		gr.update(visible=False),                       # forgotten password btn
	]


def update_interface(language: str, is_register: bool, lemma_input_type_value: str, nerc_input_type_value: str, session_state) -> list[Any]:
	"""Update key UI labels/values when language changes.

	Returns a list of gr.update objects matching the outputs wired in ui.py.
	For simplicity and robustness, we update the most visible elements.
	"""
	# switch language globally
	set_language(language)

	# Calculate values possibly dependent on register mode
	modal_title = t('authentication.register_modal_title') if is_register else t('authentication.login_modal_title')
	modal_login_text = t('authentication.register_button') if is_register else t('authentication.login_button')
	switch_text = t('authentication.switch_to_login') if is_register else t('authentication.switch_to_register')

	# Determine which option was selected before language change, across any locale
	# Build cross-language sets for text/file options
	text_opts: set[str] = set()
	file_opts: set[str] = set()
	cur_lang = get_current_language()
	for lg in get_available_languages():
		set_language(lg)
		text_opts.add(t('nlp.text_input_option'))
		file_opts.add(t('nlp.file_upload_option'))
	# restore language after probing
	set_language(language)
	# Map previous values to new language equivalents
	lemma_selected_is_text = lemma_input_type_value in text_opts
	nerc_selected_is_text = nerc_input_type_value in text_opts  # note: same keys

	lemma_radio_value = t('nlp.text_input_option') if lemma_selected_is_text else t('nlp.file_upload_option')
	nerc_radio_value = t('nlp.text_input_option') if nerc_selected_is_text else t('nlp.file_upload_option')

	new_session_state = {"access_token": session_state["access_token"], "language": language}

	return [
		# 1 header markdown
		gr.update(value=t('header.title')),
		# 2-5 header buttons
		gr.update(value=t('header.login_button')),
		gr.update(value=t('header.federated_login_button')),
		gr.update(value=t('header.profile_button')),
		gr.update(value=t('header.logout_button')),
		# 6-7 tab labels
		gr.update(label=t('tabs.lemmatizer')),
		gr.update(label=t('tabs.nerc')),
		# 8-9 intro markdowns
		gr.update(value=f"""
					{t('lemmatizer.title')}
					{t('lemmatizer.description')}
					"""),
		gr.update(value=f"""
					{t('nerc.title')}
					{t('nerc.description')}
					"""),
		# 10-14 Lemma controls: Radio label/choices/value, textbox label/placeholder, file label, analyze button, output label
		gr.update(label=t('nlp.input_type_label'), choices=[t('nlp.text_input_option'), t('nlp.file_upload_option')], value=lemma_radio_value),
		gr.update(label=t('nlp.text_input_label'), placeholder=t('nlp.text_input_placeholder')),
		gr.update(label=t('nlp.file_upload_label')),
		gr.update(value=t('nlp.analyze_button')),
		gr.update(value=t('nlp.results_label')),
		gr.update(
			choices=[
				t('nlp.output_format_web'),
				"txt",
				"json"
			],
			value=t('nlp.output_format_web'),
			label=t('nlp.output_format_label'),
		),
		# 15-19 NERC controls
		gr.update(label=t('nlp.input_type_label'), choices=[t('nlp.text_input_option'), t('nlp.file_upload_option')], value=nerc_radio_value),
		gr.update(label=t('nlp.text_input_label'), placeholder=t('nlp.text_input_placeholder')),
		gr.update(label=t('nlp.file_upload_label')),
		gr.update(value=t('nlp.analyze_button')),
		gr.update(value=t('nlp.results_label')),
		gr.update(
			choices=[
				t('nlp.output_format_web'),
				"txt",
				"json"
			],
			value=t('nlp.output_format_web'),
			label=t('nlp.output_format_label'),
		),
		# 20-28 Login modal texts
		gr.update(value=modal_title),
		gr.update(label=t('authentication.username_label'), placeholder=t('authentication.username_placeholder')),
		gr.update(label=t('authentication.email_label'), placeholder=t('authentication.email_placeholder')),
		gr.update(label=t('authentication.password_label')),
		gr.update(label=t('authentication.password_confirm_label')),
		gr.update(value=modal_login_text),
		gr.update(value=t('authentication.cancel_button')),
		gr.update(value=switch_text),
		gr.update(value=t('authentication.forgot_password')),
		# 29-33 Email verification modal basics
		gr.update(value=t('email_verification.modal_title')),
		gr.update(label=t('email_verification.code_label'), placeholder=t('email_verification.code_placeholder')),
		gr.update(value=t('email_verification.resend_button')),
		gr.update(value=t('email_verification.verify_button')),
		gr.update(value=t('email_verification.close_button')),
		# 34-39 Profile modal basics
		gr.update(value=t('profile.modal_title')),
		gr.update(value=t('profile.resend_verification_button')),
		gr.update(value=t('profile.generate_key_button')),
		gr.update(value=t('profile.logout_button')),
		gr.update(value=t('profile.close_button')),
		gr.update(value=t('profile.okay_button')),
		# 40-47 Password reset modal basics
		gr.update(value=t('password_reset.modal_title')),
		gr.update(label=t('password_reset.code_label'), placeholder=t('password_reset.code_placeholder')),
		gr.update(label=t('password_reset.email_label'), placeholder=t('password_reset.email_placeholder')),
		gr.update(label=t('password_reset.password_label')),
		gr.update(label=t('password_reset.password_confirm_label')),
		gr.update(value=t('password_reset.resend_button')),
		gr.update(value=t('password_reset.verify_button')),
		gr.update(value=t('password_reset.close_button')),
		# 48-51 Password request (email-only)
		gr.update(value=t('password_reset.request_modal_title')),
		gr.update(label=t('password_reset.email_label'), placeholder=t('password_reset.email_placeholder')),
		gr.update(value=t('password_reset.request_send_button')),
		gr.update(value=t('password_reset.close_button')),
		new_session_state
	]


# Toggle visibility based on input type for Lemmatizer
def toggle_lemma_visibility(input_type):
	if input_type == t('nlp.text_input_option'):
		return [
			gr.update(visible=True),							# Text input
			# gr.update(visible=False, value=None),				# File upload
			gr.update(visible=False),				# File upload
			gr.update(value=t('nlp.analyze_text_button'))  # Button text
		]
	else:
		return [
			# gr.update(visible=False, value=None),  # Text input
			gr.update(visible=False),  # Text input
			gr.update(visible=True),   # File upload
			gr.update(value=t('nlp.analyze_file_button'))  # Button text
		]


# Toggle visibility based on input type for NERC
def toggle_nerc_visibility(input_type):
	if input_type == t('nlp.text_input_option'):
		return [
			gr.update(visible=True),  						# Text input
			gr.update(visible=False),			# File upload
			# gr.update(visible=False, value=None),			# File upload
			gr.update(value=t('nlp.analyze_text_button'))	# Button text
		]
	else:
		return [
			# gr.update(visible=False, value=None),			# Text input
			gr.update(visible=False),			# Text input
			gr.update(visible=True),						# File upload
			gr.update(value=t('nlp.analyze_file_button'))	# Button text
		]

# ----------------------------------------------------------------------------
# Authentication / profile helpers
# ----------------------------------------------------------------------------

def handle_modal_login(username, email, password, password_confirm, current_state, is_register):
	"""Handles both registration and login flows and returns exactly 12 outputs to match `modal_login_btn` wiring."""
	# Expected outputs:
	# [auth_state, login_message, login_btn, federated_login_btn, profile_btn, user_info,
	#  logout_btn, login_modal, username_input, password_input, main_content, email_verification_modal]
	
	# Helper to create a failure response with the correct number of outputs
	def create_failure_response(state, message):
		return [
			state,  # auth_state
			gr.update(value=message),  # login_message
			gr.update(),  # login_btn
			gr.update(),  # federated_login_btn
			gr.update(),  # profile_btn
			gr.update(),  # user_info
			gr.update(),  # logout_btn
			gr.update(visible=True),  # login_modal
			gr.update(),  # username_input
			gr.update(),  # password_input
			gr.update(visible=False),  # main_content
			gr.update(visible=False)  # email_verification_modal
		]
	try:
		# Registration flow
		if is_register:
			if not all([username, email, password, password_confirm]):
				return create_failure_response(
					current_state,
					t('messages.errors.fill_all_fields')
				)
				
			if password != password_confirm:
				return create_failure_response(
					current_state,
					t('messages.errors.passwords_not_match')
				)
			
			# Enforce minimum and maximum username length
			if len(username) < int(USERNAME_MIN_LENGTH):
				return create_failure_response(
					current_state,
					t('messages.errors.username_too_short')
				)
			elif len(username) > int(USERNAME_MAX_LENGTH):
				return create_failure_response(
					current_state,
					t('messages.errors.username_too_long')
				)
			
			# Enforce minimum and maximum password length
			if len(password) < int(PASSWORD_MIN_LENGTH):
				return create_failure_response(
					current_state,
					t('messages.errors.password_too_short') 
				)
			elif len(password) > int(PASSWORD_MAX_LENGTH):
				return create_failure_response(
					current_state,
					t('messages.errors.password_too_long')
				)
			
			success, username, token, status, error_msg, count, status_code = api.register_user(username, email, password)
			
			if not success:
				if error_msg and error_msg == "PasswordNotSecure":
					if count:
						if count > 100000:
							msg = t('messages.errors.password_not_secure_100000')
						elif count > 1000:
							msg = t('messages.errors.password_not_secure_1000')
						else:
							msg = t('messages.errors.password_not_secure')
				elif status_code and status_code == 409:
					msg = t('messages.errors.username_or_email_taken')
				else:
					# Return generic error message for registration failures
					msg = t('messages.errors.registration_failed')
				
				return create_failure_response(
					current_state,
					msg
				)
				
			# Registration successful
			current_state = {
				"authenticated": True,
				"token": token,
				"status": status
			}
			
			# If email verification is required
			if status == "pending":
				success, message, email = api.send_verification_code(token)
				return [
					current_state,  # auth_state
					gr.update(value=""),  # login_message
					gr.update(visible=False),  # login_btn
					gr.update(visible=False),  # federated_login_btn
					gr.update(visible=True),  # profile_btn
					gr.update(visible=True, value=f"👤 ✅ **{username}**"),  # user_info
					gr.update(visible=True),  # logout_btn
					gr.update(visible=False),  # login_modal
					gr.update(value=""),  # username_input
					gr.update(value=""),  # password_input
					gr.update(visible=False),  # main_content stays hidden while verifying
					gr.update(visible=True)    # email_verification_modal
				]
		
		# Login flow
		else:
			if not username or not password:
				return create_failure_response(
					current_state,
					t('messages.errors.enter_credentials')
				)
				
			success, username, token, status = api.authenticate_user(username, password)
			if not success:
				if status == "429":
					return create_failure_response(
						current_state,
						t('messages.errors.too_many_attempts')
					)
				# Always return the same generic message for security
				return create_failure_response(
					current_state,
					t('messages.errors.invalid_credentials')
				)
				
			current_state = {
				"authenticated": True,
				"token": token,
				"status": status
			}
		
		# Common success response
		return [
			current_state,  # auth_state
			gr.update(value=""),  # login_message
			gr.update(visible=False),  # login_btn
			gr.update(visible=False),  # federated_login_btn
			gr.update(visible=True),  # profile_btn
			gr.update(visible=True, value=f"👤 ✅ **{username}**"),  # user_info
			gr.update(visible=True),  # logout_btn
			gr.update(visible=False),  # login_modal
			gr.update(value=""),  # username_input
			gr.update(value=""),  # password_input
			gr.update(visible=True),  # main_content visible on successful login
			gr.update(visible=False)  # email_verification_modal
		]
	except Exception as exc:
		return create_failure_response(
			current_state,
			t('messages.errors.api_error')
		)

def check_existing_session(request: gr.Request, auth_state, session_state):
	"""Detect existing session using the browser cookie and populate auth_state.

	Logic:
	- Read JWT from browser cookie `access_token` available via `request.cookies`.
	- If present, validate it by fetching the profile using `api.get_profile(token)`.
	- On success, update `auth_state` and show the user info. Otherwise, return unchanged UI.
	- We avoid using server-side session checks that lack the browser cookie context.
	"""
	try:

		lang = session_state["language"] if session_state["language"] else i18n.get_current_language()


		# Retrieve the token from the browser cookie if federated user
		if request and getattr(request, "cookies", None):
			token = request.cookies.get("access_token")
			if not token:
				token = session_state["access_token"]
			else:
				session_state["access_token"] = token
		else:
			token = session_state["access_token"]

		if not token:
			# No cookie from browser -> nothing to do
			return auth_state, session_state, gr.update(), lang

		# 2) Validate token by fetching user profile
		ok, data = api.get_profile(token)
		if not ok or not data:
			# Invalid/expired token; leave UI as-is and remove access_token from auth_state and session_state
			auth_state["token"] = None
			auth_state["authenticated"] = False
			auth_state["status"] = None
			session_state["access_token"] = None
			return auth_state, session_state, gr.update(), lang

		username = data.get("username") or ""
		status = data.get("u_status")

		# 3) Update auth state and UI
		auth_state["authenticated"] = True
		auth_state["status"] = status
		auth_state["token"] = token
		user_info = gr.update(visible=True, value=f"👤 ✅ **{username}**")
		return auth_state, session_state, user_info, lang

	except Exception as e:
		return auth_state, session_state, gr.update(), i18n.get_current_language()



def handle_logout(current_state, session_state):
	"""Handle user logout by resetting the authentication state.
	
	Returns:
		list: List of Gradio component updates to reset the UI to logged out state.
	"""
	# if api.logout(current_state["token"]):
	new_state = {"authenticated": False, "username": None, "token": None}
	
	# Update header to show login button and hide profile/logout
	login_btn, federated_login_btn, profile_btn, user_info, logout_btn = update_header_auth_state(False)

	new_session_state = {"access_token": None, "language": session_state["language"]}
	
	# auth_state, session_state, login_btn, federated_login_btn, profile_btn, user_info, logout_btn, profile_md, profile_modal, main_content

	# Return the new state and all UI updates
	return [
		new_state,
		new_session_state,
		login_btn,
		federated_login_btn,
		profile_btn,
		user_info,
		logout_btn,
		gr.update(value=""),  # Clear profile markdown
		gr.update(visible=False),  # Hide profile modal
		gr.update(visible=True)  # Show main content
	]
	
	# return [current_state] + session_state + update_header_auth_state(True) + [gr.update(visible=True)] + [gr.update(visible=False)]


# Update UI based on auth state changes
def update_from_auth_state(auth_state, language: str):
	logged = auth_state["authenticated"]
	return [
		{"access_token": auth_state["token"], "language": language},  # session_state
		gr.update(visible=not logged),          # login_btn
		gr.update(visible=not logged),          # federated_login_btn
		gr.update(visible=logged),              # user_info
		gr.update(visible=logged),              # profile_btn
		gr.update(visible=logged),              # logout_btn
		gr.update(interactive=logged),          # input_type (NERC)
		gr.update(interactive=logged),          # nerc_btn
		gr.update(interactive=logged),          # lemma_btn
		gr.update(interactive=logged),          # lemma_input_type
		gr.update(interactive=logged),          # lemma_output_format
		gr.update(interactive=logged)           # nerc_output_format
	]


def handle_resend_verification(state):
	"""Handle resending the verification email to the user.
	
	Args:
		state (dict): Current authentication state containing the user's token.
		
	Returns:
		tuple: A tuple containing updates for the verification message, verification modal, and profile modal.
	"""
	token = state.get("token")
	if not token:
		return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
	try:
		success, message, email = api.send_verification_code(token)
		if success:
			verification_message = t('messages.success.verification_sent')
		else:
			verification_message = t('messages.errors.verification_not_sent')
		
		return gr.update(value=verification_message), gr.update(visible=True), gr.update(visible=False)

	except Exception as e:
		return gr.update(value=f"Error: {str(e)}"), gr.update(visible=True), gr.update(visible=False)


def verify_email(state, code):
	"""Verify the user's email with the provided verification code.

	Args:
		state (dict): Current authentication state containing the user's token.
		code (str): Verification code sent to the user's email.
		
	Returns:
		tuple: A tuple containing updates for the verification message, 
				verification modal visibility, and profile modal visibility.
	"""
	token = state.get("token")
	if not token:
		return gr.update(value=t('messages.errors.not_authenticated')), gr.update(visible=True), gr.update(visible=False)
	try:
		# Call verify-email endpoint
		success, verified = api.verify_email(token, code)

		if success:
			return (
				gr.update(value=t('messages.success.email_verified')),	# email_verification_message
				gr.update(visible=not verified),						# email_verification_modal
				gr.update(visible=verified)  							# main_content
			)
		else:
			return (
				gr.update(value=t('messages.errors.verification_failed')),	# email_verification_message
				gr.update(visible=True),								# email_verification_modal
				gr.update(visible=False)								# main_content
			)
	except Exception as e:
		return (
			gr.update(value=t('messages.errors.verification_failed') + f": {str(e)}"),  # email_verification_message
			gr.update(visible=True),								# email_verification_modal
			gr.update(visible=False)								# main_content
		)

# ----------------------------------------------------------------------------
# Password reset helpers
# ----------------------------------------------------------------------------

def handle_request_password_reset(email):
	"""Send password reset code to the given email."""
	if not email:
		return gr.update(value=t('messages.errors.email_required'))
	success, message = api.request_password_reset(email)
	if success:
		return gr.update(value=t('messages.success.password_reset_sent'))
	return gr.update(value=t('messages.errors.password_reset_failed'))


def handle_password_reset_verify(code, password, password_confirm):
	"""Verify code and set new password."""
	if not all([code, password, password_confirm]):
		return [gr.update(value=t('messages.errors.fill_all_fields')), gr.update(visible=True)]
	if password != password_confirm:
		return [gr.update(value=t('messages.errors.passwords_not_match')), gr.update(visible=True)]
	# Enforce minimum password length for reset as well
	if len(password) < 12:
		return [gr.update(value=t('messages.errors.password_too_short')), gr.update(visible=True)]
	success, message = api.reset_password(code, password)
	if success:
		# Success -> close modal
		return ["OK", gr.update(visible=False)]
	return [gr.update(value=t("messages.errors.password_reset_failed")), gr.update(visible=True)]


def init_from_url(request: gr.Request, nav_state_value: dict):
	"""Initialize UI from URL query params.

	If `email` and `token` are provided, open the password reset modal and prefill
	the corresponding inputs while hiding them (so the user only enters the new password).

	Returns a list of updates to match the outputs wired in ui.py demo.load.
	"""
	# Default: keep everything as-is (no modal), do not change inputs
	default_nav = navigate_to_modal(None, nav_state_value, close_tabs=False)
	# default_nav returns: [nav_state, login, profile, email_verif, password_request, password_reset, api_key, tabs]
	# We need to also return reset_email_input and reset_code_input updates at the end.

	# Extract from URL query params
	try:
		qp = request.query_params  # Starlette QueryParams
		token = qp.get("t") if qp else None
	except Exception:
		token = None

	if not token:
		return default_nav + [gr.update(), gr.update()]

	# Open password reset modal, hide request modal, keep others hidden
	nav_updates = navigate_to_modal("password_reset", nav_state_value)

	# Prefill email and token, hide those fields
	email_update = gr.update(value="", visible=False)
	token_update = gr.update(value=token, visible=False)

	return nav_updates + [email_update, token_update]



def send_verification_code(token: str):
	return api.send_verification_code(token)


def get_profile_info(state: dict):
	token = state.get("token")
	if not token:
		return (
			gr.update(value=t('messages.errors.not_authenticated')),
			gr.update(visible=True),
			gr.update(visible=False),
			gr.update(visible=True),
		)
	ok, data = api.get_profile(token)
	if not ok:
		return (
			gr.update(value=t('messages.errors.profile_not_found')),
			gr.update(visible=True),
			gr.update(visible=False),
			gr.update(visible=True),
		)
	username = data.get("username", "")
	email = data.get("email", "")
	verified = data.get("email_verified", False)
	verified_msg = "" if verified else t('messages.formatting.email_not_verified')
	api_key_preview = data.get("api_key_preview", t('messages.formatting.no_api_key'))
	md = (
		f"{t('profile_info.username_label')} {username}\n\n"
		f"{t('profile_info.email_label')} {email} {verified_msg}\n\n"
		f"{t('profile_info.api_key_label')} {api_key_preview}"
	)
	return (
		gr.update(value=md),        # profile_md
		gr.update(visible=True),    # profile_modal
		gr.update(visible=False if verified else True), # resend_verification_btn2
		gr.update(visible=False),   # main_content
	)


# ----------------------------------------------------------------------------
# API Key operations
# ----------------------------------------------------------------------------

def create_api_key(state: dict):
	"""Generate a new API key for the authenticated user.

	Parameters
	----------
	state : dict
		Authentication state holding the JWT token.

	Returns
	-------
	tuple
		Updates for api_key_modal_md, api_key_modal visibility, profile_modal visibility.
	"""
	token = state.get("token")
	if not token:
		return (
			gr.update(value=t('messages.errors.authentication_required')),
			gr.update(visible=True),  # show modal with error
			gr.update(visible=False),  # hide profile modal
		)

	success, data = api.generate_api_key(token)
	if success and data:
		full_key = data.get("api_key")
		preview = data.get("api_key_preview", "")
		# Show a generic instruction from translations and append the key outside of i18n
		msg = (
			t('messages.success.new_api_key')
			+ f"\n\n<div style='font-size: 16px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;'>"
			+ t('messages.success.api_key_instructions')
			+ f"\n\n<code style='font-size: 16px; font-family: \"Monaco\", \"Menlo\", \"Ubuntu Mono\", monospace; color: white; letter-spacing: 1px; font-weight: 600; word-break: break-all; line-height: 1.6; background: #2d3748; padding: 12px; border-radius: 4px; display: inline-block;'>{full_key}</code>"
			+ "</div>\n\n"
		)
	else:
		msg = t('messages.errors.api_key_generation_failed')
	return (
		gr.update(value=msg),
		gr.update(visible=True),
		gr.update(visible=False),
	)


# ----------------------------------------------------------------------------
# NLP operations
# ----------------------------------------------------------------------------

def lemmatize_text(text: str, file_path: str, state: Dict[str, Any], output_format: str, lemma_input_type):

	if not text.strip() and not file_path:
		return [f"<span style='color:orange'>{t('messages.warnings.enter_text_or_file')}</span>", gr.update(value=None, visible=False)]

	if lemma_input_type == t('nlp.text_input_option'):
		text = text.strip()
		file_path = None
	else:
		file_path = file_path
		text = None

	token = state.get("token")
	status = state.get("status")

	headers: Dict[str, str] = {}
	
	# Set up authentication headers if token exists
	if token:
		headers["Authorization"] = f"Bearer {token}"
		if status == "disabled":
			return [f"<span style='color:orange'>{t('messages.errors.account_disabled')}</span>", gr.update(value=None, visible=False)]
	
	try:
		# Handle file upload
		if file_path:
			allowed_exts = {'.txt', '.pdf'}
			_, ext = os.path.splitext(file_path.lower())
			if ext not in allowed_exts:
				return [f"<span style='color:orange'>{t('messages.warnings.unsupported_file_type')}</span>", gr.update(value=None, visible=False)]
			
			
			if token and status != "pending":
				post_file_fn = api.post_lemmatizer_file
			
			resp = post_file_fn(file_path, headers)
		# Handle text input
		else:
			post_fn = api.post_lemmatizer_guest
			if token and status != "pending":
				post_fn = api.post_lemmatizer
				
			headers["Content-Type"] = "application/json"
			resp = post_fn(text, headers)
		
		# Process response
		if resp.status_code == 200:
			result_json = resp.json()
			html_view = formatters.format_lemmatized_result(result_json)

			# Handle download formats
			fmt = (output_format or t('nlp.output_format_web')).strip().lower()
			if fmt == "json":
				with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tf:
					json.dump(result_json, tf, ensure_ascii=False, indent=2)
					temp_path = tf.name
				return [gr.update(value=html_view, visible=False), gr.update(value=temp_path, visible=True)]
			elif fmt == "txt":
				content = formatters.format_lemmatized_text(result_json)
				with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tf:
					tf.write(content)
					temp_path = tf.name
				return [gr.update(value=html_view, visible=False), gr.update(value=temp_path, visible=True)]
			# Default: web only
			return [html_view, gr.update(value=None, visible=False)]
		elif resp.status_code == 400:
			return [f"<span style='color:orange'>{t('messages.warnings.invalid_input')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 401:
			return [f"<span style='color:orange'>{t('messages.warnings.authentication_required')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 413:
			return [f"<span style='color:orange'>{t('messages.warnings.file_too_large')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 415:
			return [f"<span style='color:orange'>{t('messages.warnings.unsupported_file_type')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 429:
			msg = t('messages.warnings.rate_limit_guest') if not token else t('messages.warnings.rate_limit_user')
			return [f"<span style='color:orange'>{msg}</span>", gr.update(value=None, visible=False)]
		# Use a generic error message and append details outside of i18n
		return [f"<span style='color:red'>{t('messages.errors.api_error')} ({resp.status_code})</span>", gr.update(value=None, visible=False)]
	except FileNotFoundError:
		return [f"<span style='color:red'>{t('messages.errors.file_not_found')}</span>", gr.update(value=None, visible=False)]
	except Exception as exc:
		return [f"<span style='color:red'>{t('messages.errors.api_call_failed')}</span>", gr.update(value=None, visible=False)]
		# return [f"<span style='color:red'>{str(exc)}</span>", gr.update(value=None, visible=False)]


def recognize_entities(text: str, file_path: str, state: Dict[str, Any], output_format: str, nerc_input_type):
	if not text.strip() and not file_path:
		return [f"<span style='color:orange'>{t('messages.warnings.enter_text_or_file')}</span>", gr.update(value=None, visible=False)]

	if nerc_input_type == t('nlp.text_input_option'):
		text = text.strip()
		file_path = None
	else:
		file_path = file_path
		text = None

	token = state.get("token")
	status = state.get("status")

	headers: Dict[str, str] = {}
	
	# Set up authentication headers if token exists
	if token:
		headers["Authorization"] = f"Bearer {token}"
		if status == "disabled":
			return [f"<span style='color:orange'>{t('messages.errors.account_disabled')}</span>", gr.update(value=None, visible=False)]
	
	try:
		# Handle file upload
		if file_path:
			allowed_exts = {'.txt', '.pdf'}
			_, ext = os.path.splitext(file_path.lower())
			if ext not in allowed_exts:
				return [f"<span style='color:orange'>{t('messages.warnings.unsupported_file_type')}</span>", gr.update(value=None, visible=False)]

			try:
				original_text = file_processor(file_path)				
			except Exception as e:
				original_text = None
			#original_text = extracted_text if extracted_text.strip() else None

			if token and status != "pending":
				post_file_fn = api.post_nerc_file
				
			resp = post_file_fn(file_path, headers)
		# Handle text input
		else:
			original_text = text
			post_fn = api.post_nerc_guest
			if token and status != "pending":
				post_fn = api.post_nerc
				
			headers["Content-Type"] = "application/json"
			resp = post_fn(text, headers)
		
		# Process response
		if resp.status_code == 200:
			data = resp.json()
			# For text input, pass the original text to enable inline highlighting.
			# For file uploads, keep fallback chip rendering unless we can read .txt
			
			#original_text = None if file_path else text
			html_view = formatters.format_nerc_result(data, original_text=original_text)

			fmt = (output_format or t('nlp.output_format_web')).strip().lower()
			if fmt == "json":
				import tempfile, json
				with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tf:
					json.dump(data, tf, ensure_ascii=False, indent=2)
					temp_path = tf.name
				return [gr.update(value=html_view, visible=False), gr.update(value=temp_path, visible=True)]
			elif fmt == "txt":
				import tempfile
				txt_content = ""
				# Prefer bracketed original text when available
				if original_text:
					txt_content = formatters.format_nerc_bracketed_text(original_text, data.get("emaitza", {}))
				elif file_path:
					_, ext = os.path.splitext(file_path.lower())
					if ext == ".txt":
						try:
							with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
								file_text = f.read()
							txt_content = formatters.format_nerc_bracketed_text(file_text, data.get("emaitza", {}))
						except Exception:
							# Fallback to simple list if reading fails
							pass
				# Fallback to a list of entities if we couldn't build bracketed text
				if not txt_content:
					pairs = []
					for ent, etype in (data.get("emaitza", {}) or {}).items():
						if ent is None:
							continue
						pairs.append(f"{str(ent).strip()}\t{str(etype).upper()}")
					txt_content = "\n".join(pairs)

				with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tf:
					tf.write(txt_content)
					temp_path = tf.name
				return [gr.update(value=html_view, visible=False), gr.update(value=temp_path, visible=True)]
			# Default web only
			return [html_view, gr.update(value=None, visible=False)]
		elif resp.status_code == 401:
			return [f"<span style='color:orange'>{t('messages.warnings.authentication_required')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 413:	
			return [f"<span style='color:orange'>{t('messages.warnings.file_too_large')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 415:
			return [f"<span style='color:orange'>{t('messages.warnings.unsupported_file_type')}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 429:
			msg = t('messages.warnings.rate_limit_guest') if not token else t('messages.warnings.rate_limit_user')
			return [f"<span style='color:orange'>{msg}</span>", gr.update(value=None, visible=False)]
		elif resp.status_code == 499:
			return [f"<span style='color:orange'>{t('messages.warnings.request_timeout')}</span>", gr.update(value=None, visible=False)]
		return [f"<span style='color:red'>{t('messages.errors.api_error')}</span>", gr.update(value=None, visible=False)]
	except FileNotFoundError:
		return [f"<span style='color:red'>{t('messages.errors.file_not_found')}</span>", gr.update(value=None, visible=False)]
	except Exception as exc:
		return [f"<span style='color:red'>{t('messages.errors.api_call_failed')}</span>", gr.update(value=None, visible=False)]
