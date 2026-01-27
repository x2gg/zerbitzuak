import hmac
import os
import requests
import gradio as gr

# Shared HTTP session to preserve cookies (e.g., access-token)
session = requests.Session()

# API URLs
APISIX_URL = os.getenv("APISIX_URL", "https://zerbitzuak.hitz.eus/api")
USERS_API_URL = f"{APISIX_URL}/users/"
PROFILES_API_URL = f"{APISIX_URL}/profiles/"

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:7860")


#############################
## URL ETA ALDAGAI BERRIAK ##
#############################
APISIX_URL: str = os.getenv("APISIX_URL", "https://zerbitzuak.hitz.eus/api")
DEFAULT_HEADERS = {
	"Content-Type": "application/json",
}


# --- AUTHENTICATION FUNCTIONS ---

# def check_existing_session(authenticated):
# 	"""On load, show app only if authenticated is True."""
# 	if authenticated:
# 		return (
# 			gr.update(visible=False),  # login_panel
# 		)
# 	return (
# 		gr.update(visible=True),            # login_panel
# 	)

def do_login(username: str, password: str, auth_state):
	"""Login from API"""
	table = initial_table_load(auth_state)
	auth_state["access_token"] = None
	try:
		response = session.post(
			f"{APISIX_URL}/crud_login",
			headers=DEFAULT_HEADERS,
			json={"username": username, "password": password},
			timeout=10,
		)

		data = response.json()
		retry_after = response.headers.get("Retry-After")
		if retry_after:
			retry_after = int(retry_after)

		if data.get("http_code") == 200 and data.get("access_token"):
			# return True, username, data.get("access_token")
			auth_state["access_token"] = data.get("access_token")
			return (
				gr.update(visible=True),	# tabs
				gr.update(visible=False),	# login_panel
				gr.update(value="", visible=False),  # login_message
				gr.update(visible=True),	# logout_btn
				auth_state,					# auth_state
				table,						# initial users table
			)
		elif data.get("http_code") == 429:
			# return False, None, None, "429"
			return (
				gr.update(visible=False),  # tabs
				gr.update(visible=True),   # login_panel
				gr.update(value=f"Too many attempts. Retry after a few minutes", visible=True),  # login_message
				gr.update(visible=False),  # logout_btn
				auth_state,     			# auth_state
				table,                     # initial users table
			)
		return (
			gr.update(visible=False),  # tabs
			gr.update(visible=True),   # login_panel
			gr.update(value="Invalid username or password", visible=True),  # login_message
			gr.update(visible=False),  # logout_btn
			auth_state,     			# auth_state
			table,                     # initial users table
		)
	except Exception:
		# Silent fail – caller decides message
		return (
			gr.update(visible=False),  # tabs
			gr.update(visible=True),   # login_panel
			gr.update(value="Invalid username or password", visible=True),  # login_message
			gr.update(visible=False),  # logout_btn
			auth_state,     			# auth_state
			table,                     # initial users table
		)


def do_logout(auth_state):
	"""Logout and clear local session cookies."""
	auth_state["access_token"] = None
	return (
		gr.update(visible=False),	# tabs
		gr.update(visible=True),	# login_panel
		gr.update(value="", visible=False),  # login_message
		gr.update(visible=False),	# logout_btn
		auth_state,					# auth_state
		gr.update(value=""),		# login_user
		gr.update(value=""),		# login_pass
	)

def change_panel(panel):
	# Change between login_panel, users_panel, new_user_panel and edit_user_panel
	if panel == "list_panel":
		return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
	elif panel == "new_panel":
		return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
	elif panel == "edit_panel":
		return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
	else:
		# Hide all
		return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def show_login_panel():
	users_panel, new_user_panel, edit_user_panel = change_panel("hide")
	profiles_panel, new_profile_panel, edit_profile_panel = change_panel("hide")
	return gr.update(visible=True), users_panel, new_user_panel, edit_user_panel, profiles_panel, new_profile_panel, edit_profile_panel


# --- PROFILES FUNCTIONS ---

def hide_profiles():
	profiles_panel, new_profile_panel, edit_profile_panel = change_panel("hide")
	return profiles_panel, new_profile_panel, edit_profile_panel

def show_profiles_panel():
	profiles_panel, new_profile_panel, edit_profile_panel = change_panel("list_panel")
	return profiles_panel, new_profile_panel, edit_profile_panel

def show_new_profile_panel():
	"""Show the new user panel when the New User button is clicked"""
	profiles_panel, new_profile_panel, edit_profile_panel = change_panel("new_panel")
	return profiles_panel, new_profile_panel, edit_profile_panel

def show_edit_profile_panel():
	profiles_panel, new_profile_panel, edit_profile_panel = change_panel("edit_panel")
	return profiles_panel, new_profile_panel, edit_profile_panel

def fetch_profiles(token):
	try:
		response = session.get(PROFILES_API_URL, headers={"Authorization": f"Bearer {token}"})
		return response.json() if response.status_code == 200 else []
	except requests.exceptions.RequestException:
		return []

def get_profile_names(auth_state):
	"""Get available user types from profiles"""
	try:
		token = auth_state["access_token"] if auth_state else None
		profiles = fetch_profiles(token)
		# Ensure profiles is a list and has items
		if not isinstance(profiles, list):
			return []
		# Extract profile types, handling potential missing 'u_type' keys
		profile_names = []
		for profile in profiles:
			if isinstance(profile, dict) and 'u_type' in profile and profile['u_type']:
				profile_names.append(profile['u_type'])
		return sorted(list(set(profile_names)))  # Remove duplicates and sort
	except Exception as e:
		print(f"Error fetching profile names: {e}")
		return []
	# Ensure we always have default profile types available
	# default_profiles = ["basic", "pro"]
	# for default_profile in default_profiles:
	# 	if default_profile not in profile_names:
	# 		profile_names.append(default_profile)

	return profile_names

def render_profiles_table(profiles):
	html = """
	<div style='text-align: center; margin: 0 auto; max-width: 800px;'>
	<table class='user-table'>
		<thead>
			<tr>
				<th>ID</th>
				<th>Name</th>
				<th>Count</th>
				<th>Time Window</th>
				<th>Rejected Code</th>
				<th>Rejected Message</th>
				<th>Policy</th>
				<th>Show Limit Header</th>
				<th>Actions</th>
			</tr>
		</thead>
		<tbody>
	"""
	for profile in profiles:
		html += f"""
		<tr>
			<td>{profile['id']}</td>
			<td>{profile['u_type']}</td>
			<td>{profile['count']}</td>
			<td>{profile['time_window']}</td>
			<td>{profile['rejected_code']}</td>
			<td>{profile['rejected_msg']}</td>
			<td>{profile['policy'].capitalize()}</td>
			<td>{'Yes' if profile.get('show_limit_quota_header') else 'No'}</td>
			<td>
				<button class='btn btn-icon' onclick="window.location.href='?profile_id={profile['id']}';">Edit</button>
			</td>
		</tr>
		"""
	html += "</tbody></table>"
	html += "</div>"
	return html

def fetch_profile(token, profile_id):
	try:
		response = session.get(f"{PROFILES_API_URL}{profile_id}", headers={"Authorization": f"Bearer {token}"})
		if response.status_code == 200:
			return response.json()
	except Exception as e:
		print(f"Error fetching profile: {e}")
	return None

def update_profile(token, profile_id, u_type, count, time_window, rejected_code, rejected_msg, policy, show_limit_quota_header):
	data = {
		"u_type": u_type,
		"count": count,
		"time_window": time_window,
		"rejected_code": rejected_code,
		"rejected_msg": rejected_msg,
		"policy": policy,
		"show_limit_quota_header": show_limit_quota_header
	}
	try:
		resp = session.put(f"{PROFILES_API_URL}{profile_id}", headers={"Authorization": f"Bearer {token}"}, json=data)
		return resp.status_code == 200
	except Exception as e:
		print(f"Error updating profile: {e}")
	return False

def extract_profile_id(request: gr.Request):
	"""Extract profile_id from URL parameters"""
	if request and hasattr(request, 'query_params') and 'profile_id' in request.query_params:
		return request.query_params['profile_id']
	return ""

def auto_load_profile(profile_id, auth_state):
	if profile_id:
		token = auth_state["access_token"] if auth_state else None
		profile = fetch_profile(token, profile_id)
		if profile:
			return [
				gr.update(visible=True),  # edit_section
				profile["id"],           # profile_id_box
				profile["u_type"],       # u_type
				profile["count"],        # count
				profile["time_window"],  # time_window
				profile["rejected_code"], # rejected_code
				profile["rejected_msg"], # rejected_msg
				profile["policy"],       # policy
				profile.get("show_limit_quota_header", False), # show_limit_quota_header
				gr.update(visible=False) # msg
			]
		else:
			return [
				gr.update(visible=False), # edit_section
				"",                      # profile_id_box
				"",                      # u_type
				0,                       # count
				0,                       # time_window
				0,                       # rejected_code
				"",                      # rejected_msg
				None,                    # policy
				False,                   # show_limit_quota_header
				gr.update(visible=True, value="**Profile not found!**") # msg
			]
	return [
		gr.update(visible=False), # edit_section
		"",                      # profile_id_box
		"",                      # u_type
		0,                       # count
		0,                       # time_window
		0,                       # rejected_code
		"",                      # rejected_msg
		None,                    # policy
		False,                   # show_limit_quota_header
		gr.update(visible=False) # msg
	]

def refresh_profiles_table(auth_state):
	token = auth_state["access_token"] if auth_state else None
	profiles = fetch_profiles(token)
	return render_profiles_table(profiles)

def save_profile(auth_state, profile_id, u_type, count, time_window, rejected_code, rejected_msg, policy, show_limit_quota_header):
	token = auth_state["access_token"] if auth_state else None
	ok = update_profile(token, profile_id, u_type, count, time_window, rejected_code, rejected_msg, policy, show_limit_quota_header)
	return gr.update(
		value="**Profile updated successfully!**" if ok else "**Failed to update profile.**",
		visible=True
	)

def delete_profile(auth_state, profile_id):
	token = auth_state["access_token"] if auth_state else None
	try:
		resp = session.delete(f"{PROFILES_API_URL}{profile_id}", headers={"Authorization": f"Bearer {token}"})
		if resp.status_code == 200:
			return [
				gr.update(value=""),                      # u_type
				gr.update(value=0),                       # count
				gr.update(value=60),                      # time_window
				gr.update(value=429),                     # rejected_code
				gr.update(value=""),                      # rejected_msg
				gr.update(visible=False),                 # msg
				gr.update(visible=True, value="**Profile deleted successfully!**") # delete_msg
			]
		else:
			return [
				gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
				gr.update(visible=True, value=f"**Failed to delete profile.** (Status: {resp.status_code})"),
				gr.update(visible=False)
			]
	except Exception as e:
		return [
			gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
			gr.update(visible=True, value=f"**Error deleting profile: {e}**"),
			gr.update(visible=False)
		]

def save_new_profile(auth_state, u_type, count, time_window, rejected_code, rejected_msg, policy, show_limit_quota_header):
	token = auth_state["access_token"] if auth_state else None
	profile = {
		"u_type": u_type,
		"count": count,
		"time_window": time_window,
		"rejected_code": rejected_code,
		"rejected_msg": rejected_msg,
		"policy": policy,
		"show_limit_quota_header": show_limit_quota_header
	}
	try:
		resp = session.post(PROFILES_API_URL, headers={"Authorization": f"Bearer {token}"}, json=profile)
		if resp.status_code == 200 or resp.status_code == 201:
			return gr.update(visible=True, value="**Profile created successfully!**")
		else:
			return gr.update(visible=True, value=f"**Failed to create profile.** (Status: {resp.status_code})")
	except Exception as e:
		return gr.update(visible=True, value=f"**Error creating profile: {e}")


# --- USERS FUNCTIONS ---

def hide_users():
	users_panel, new_user_panel, edit_user_panel = change_panel("hide")
	return users_panel, new_user_panel, edit_user_panel

def show_users_panel():
	users_panel, new_user_panel, edit_user_panel = change_panel("list_panel")
	return users_panel, new_user_panel, edit_user_panel

def show_new_user_panel():
	"""Show the new user panel when the New User button is clicked"""
	users_panel, new_user_panel, edit_user_panel = change_panel("new_panel")
	return users_panel, new_user_panel, edit_user_panel

def show_edit_user_panel():
	users_panel, new_user_panel, edit_user_panel = change_panel("edit_panel")
	return users_panel, new_user_panel, edit_user_panel


def create_user_form(auth_state, include_password=False, include_user_id=False, include_delete=False, title="User Form"):
	"""Helper function to create user form components with configurable fields"""

	# Form fields container
	with gr.Column(visible=True) as form_section:
		gr.Markdown(f"# {title}")

		# Hidden user_id field for edit mode
		if include_user_id:
			user_id = gr.Textbox(label="User ID", elem_id="user_id_input", visible=False)

		# Basic form fields
		username = gr.Textbox(label="Username")
		email = gr.Textbox(label="Email")

		# Password field only for new user
		password = None
		if include_password:
			password = gr.Textbox(label="Password", type="password")

		# Common fields
		profile_names = get_profile_names(auth_state)
		u_type = gr.Dropdown(
			label="Profile", 
			choices=profile_names, 
			value=profile_names[0] if profile_names else None
		)
		u_status = gr.Dropdown(label="Status", choices=["active", "pending", "disabled"], value="pending")
		is_federated = gr.Checkbox(label="Federated User", value=False, interactive=False)

	# Buttons
	with gr.Row():
		save_btn = gr.Button("Save User" if include_password else "Save Changes", variant="primary")
		if include_delete:
			delete_btn = gr.Button("Delete User", variant="stop")
		cancel_btn = gr.Button("Cancel", variant="secondary", link=WEB_BASE_URL)

	# Messages
	delete_msg = gr.Markdown(visible=False) if include_delete else None
	msg = gr.Markdown(visible=False)

	return {
		'form_section': form_section,
		'user_id': user_id if include_user_id else None,
		'username': username,
		'email': email,
		'password': password,
		'u_type': u_type,
		'u_status': u_status,
		'is_federated': is_federated,
		'save_btn': save_btn,
		'delete_btn': delete_btn if include_delete else None,
		'cancel_btn': cancel_btn,
		'delete_msg': delete_msg,
		'msg': msg
	}

def create_profile_form(include_profile_id=False, include_delete=False, title="Profile Form"):
	"""Helper function to create profile form components with configurable fields"""

	# Form fields container
	with gr.Column(visible=True) as form_section:
		gr.Markdown(f"# {title}")

		# Hidden profile_id field for edit mode
		if include_profile_id:
			profile_id = gr.Textbox(label="Profile ID", elem_id="profile_id_input", visible=False)

		# Basic form fields
		u_type = gr.Textbox(label="Profile")
		count = gr.Number(label="Count", value=10)
		time_window = gr.Number(label="Time Window (seconds)", value=60)
		rejected_code = gr.Number(label="Rejected Code", value=429)
		rejected_msg = gr.Textbox(label="Rejected Message", value="Limit exceeded.")
		policy = gr.Dropdown(label="Policy", choices=["local"], value="local")
		show_limit_quota_header = gr.Checkbox(label="Show Limit Quota Header", value=True, interactive=True)

		# Buttons
		with gr.Row():
			save_btn = gr.Button("Save Profile" if not include_profile_id else "Save Changes", variant="primary")
			if include_delete:
				delete_btn = gr.Button("Delete Profile", variant="stop")
			cancel_btn = gr.Button("Cancel", variant="secondary", link=WEB_BASE_URL)

		# Messages
		delete_msg = gr.Markdown(visible=False) if include_delete else None
		msg = gr.Markdown(visible=False)

	return {
		'form_section': form_section,
		'profile_id': profile_id if include_profile_id else None,
		'u_type': u_type,
		'count': count,
		'time_window': time_window,
		'rejected_code': rejected_code,
		'rejected_msg': rejected_msg,
		'policy': policy,
		'show_limit_quota_header': show_limit_quota_header,
		'save_btn': save_btn,
		'delete_btn': delete_btn if include_delete else None,
		'cancel_btn': cancel_btn,
		'delete_msg': delete_msg,
		'msg': msg
	}
def initial_table_load(auth_state):
	if auth_state["access_token"]:
		token = auth_state["access_token"] if auth_state else None
		return render_table(fetch_users(token, "", "All", "All"))
	return ""

def fetch_user(token, user_id):
	try:
		response = session.get(f"{USERS_API_URL}{user_id}", headers={"Authorization": f"Bearer {token}"})
		if response.status_code == 200:
			return response.json()
	except Exception as e:
		print(f"Error fetching user: {e}")
	return None

def fetch_users(token, query="", u_type="All", u_status="All"):
	if not token:
		return []
	params = {}
	if query and query.strip():
		params["email_contains"] = query.strip()
	if u_type != "All":
		params["u_type"] = u_type.lower()
	if u_status != "All":
		params["u_status"] = u_status.lower()
	try:
		response = session.get(USERS_API_URL, headers={"Authorization": f"Bearer {token}"}, params=params)
		return response.json() if response.status_code == 200 else []
	except requests.exceptions.RequestException:
		return []

def render_table(users):
	html = """
	<div style='text-align: center; margin: 0 auto; max-width: 800px;'>
	<table class='user-table'>
		<thead>
			<tr>
				<th>User</th>
				<th>Email</th>
				<th>Type</th>
				<th>Status</th>
				<th>Federated</th>
				<th>Email verified</th>
				<th>Actions</th>
			</tr>
		</thead>
		<tbody>
	"""
	for user in users:
		u_status = user.get("u_status")
		u_type = user.get("u_type", "basic").lower()
		html += f"""
		<tr>
			<td>
				<div style='font-weight: 500;'>{user['username']}</div>
				<div style='font-size: 0.875em; color: #666'>ID: {user['id']}</div>
			</td>
			<td>{user['email']}</td>
			<td>{u_type.capitalize()}</td>
			<td>
				<div class='status {u_status}'>
					<span>●</span>
					{u_status.capitalize()}
				</div>
			</td>
			<td>{'Yes' if user.get('isFederated') else 'No'}</td>
			<td>{user.get('email_verified', 'Unknown')}</td>
			<td>
				<button class='btn btn-icon' onclick="window.location.href='?user_id={user['id']}';">Edit</button>
			</td>
		</tr>
		"""
	html += "</tbody></table>"
	html += "</div>"
	return html

def update_user(token, user_id, username, email, u_type, u_status, is_federated):
	data = {
		"username": username, 
		"email": email, 
		"u_type": u_type, 
		"u_status": u_status,
		"isFederated": is_federated
	}
	try:
		resp = session.put(f"{USERS_API_URL}{user_id}", headers={"Authorization": f"Bearer {token}"}, json=data)
		return resp.status_code == 200
	except Exception as e:
		print(f"Error updating user: {e}")
	return False

def extract_user_id(request: gr.Request):
	"""Extract user_id from URL parameters"""
	if request and hasattr(request, 'query_params') and 'user_id' in request.query_params:
		return request.query_params['user_id']
	return ""

# def update_user_type_choices(auth_state):
# 	"""Update user type dropdown choices when page loads"""
# 	profile_names = get_profile_names(auth_state)
# 	if profile_names:
# 		return gr.update(choices=profile_names)
# 	else:
# 		return gr.update(interactive=False)  # disable dropdown if no profiles exist

def auto_load_user(user_id, auth_state):
	if user_id:
		token = auth_state["access_token"] if auth_state else None
		user = fetch_user(token, user_id)
		if user:
			# Get current profile names
			profile_choices = get_profile_names(auth_state)
				
			return [
				gr.update(visible=True),  # edit_section
				user["id"],              # user_id
				user["username"],        # username
				user["email"],           # email
				gr.update(value=user["u_type"], choices=profile_choices),  # u_type
				user["u_status"],        # u_status
				user.get("isFederated", False),  # is_federated
				gr.update(visible=False) # msg
			]
	return [
		gr.update(visible=True),                                # edit_section
		gr.update(value="", interactive=False),                 # user_id
		gr.update(value="", interactive=False),                 # username
		gr.update(value="", interactive=False),                 # email
		gr.update(value=None, choices=[], interactive=False),   # u_type
		gr.update(value=None, choices=[], interactive=False),   # u_status
		gr.update(value=False, interactive=False),              # is_federated
		gr.update(visible=True, value="**User not found!**")    # msg
	]

def save_user(auth_state, user_id, username, email, u_type, u_status, is_federated):
	token = auth_state["access_token"] if auth_state else None
	ok = update_user(token, user_id, username, email, u_type, u_status, is_federated)
	return gr.update(
		value="**User updated successfully!**" if ok else "**Failed to update user.**",
		visible=True
	)

def delete_user(auth_state, user_id):
	token = auth_state["access_token"] if auth_state else None
	try:
		resp = session.delete(f"{USERS_API_URL}{user_id}", headers={"Authorization": f"Bearer {token}"})
		if resp.status_code == 200 or resp.status_code == 204:
			# Clear form fields and show success message
			return [
				"",  # username
				"",  # email
				gr.update(visible=True, value="**User deleted successfully!**"),
				gr.update(visible=False)
			]
		else:
			# Show error message
			return [
				gr.update(),  # Keep current username
				gr.update(),  # Keep current email
				gr.update(visible=True, value=f"**Failed to delete user.** (Status: {resp.status_code})"),
				gr.update(visible=False)
			]
	except Exception as e:
		return [
			gr.update(),  # Keep current username
			gr.update(),  # Keep current email
			gr.update(visible=True, value=f"**Error deleting user: {str(e)}**"),
			gr.update(visible=False)
		]

def save_new_user(auth_state, username, email, password, u_type, u_status, is_federated):
	user = {
		"username": username,
		"email": email,
		"password": password,
		"u_type": u_type,
		"u_status": u_status,
		"isFederated": is_federated
	}
	token = auth_state["access_token"] if auth_state else None
	try:
		resp = session.post(USERS_API_URL, json=user, headers={"Authorization": f"Bearer {token}"})
		if resp.status_code == 200:
			return gr.update(visible=True, value="**User created successfully!**")
		else:
			return gr.update(visible=True, value=f"**Failed to create user.** (Status: {resp.status_code})")
	except Exception as e:
		return gr.update(visible=True, value=f"**Error creating user: {e}**")

def refresh_users_table(auth_state, q, t, s):
	token = auth_state["access_token"] if auth_state else None
	users = fetch_users(token, q, t, s)
	user_types = ["All"] + get_profile_names(auth_state)
	return render_table(users), gr.update(choices=user_types)

def check_url_params(request: gr.Request):
	user_id = extract_user_id(request)
	profile_id = extract_profile_id(request)
	return user_id, profile_id