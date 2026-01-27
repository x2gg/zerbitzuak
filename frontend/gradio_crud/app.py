import gradio as gr
import handlers as h
import os

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "https://zerbitzuak.hitz.eus/erab_kudeaketa/")
# APISIX_URL: str = os.getenv("APISIX_URL", "https://zerbitzuak.hitz.eus/api")

# css = """
# .gradio-container {
#     max-width: 2000px !important;
#     margin: 0 auto;  /* Center the container */
# }
# """

with gr.Blocks(fill_width=False) as demo:
	authenticated = gr.Checkbox(label="Authenticated", visible=False)
	auth_state = gr.State({"access_token": None})
	session_state = gr.BrowserState({"access_token": None, "language": ""})
	local_storage = gr.BrowserState(["", False])

	# --- Header: Login / Logout Controls ---
	with gr.Row(elem_classes=["header"]):
		with gr.Column(scale=1):
			pass  # Empty column to push content to the right
		with gr.Column(scale=0, min_width=100):
			logout_btn = gr.Button("Logout", variant="stop", visible=False, elem_classes=["logout-btn"])
	with gr.Row():
		gr.Column(scale=1, min_width=0)
		with gr.Column(visible=False, scale=0, min_width=800) as login_panel:
			gr.Markdown("## Login")
			with gr.Row():
				login_user = gr.Textbox(label="Username")
			with gr.Row():
				login_pass = gr.Textbox(label="Password", type="password")
			login_btn = gr.Button("Login", variant="primary")
			login_message = gr.Markdown(visible=False)
		gr.Column(scale=1, min_width=0)
	
	with gr.Tabs(visible=False) as tabs:

		# Users Tab
		with gr.TabItem("Users", id="user_TabItem") as uTab:
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=True, scale=0, min_width=800) as users_panel:
					with gr.Row(elem_classes=["header"]):
						with gr.Column(scale=1):
							gr.Markdown("# User Management")
						with gr.Column(scale=0, min_width=75):
							new_user_btn = gr.Button("New", variant="stop", elem_classes=["logout-btn"])


					with gr.Column(elem_classes=["search-filter"]):
						with gr.Row():
							search = gr.Textbox(placeholder="Search by email...", show_label=False, scale=4)
						with gr.Row():
							user_type = gr.Dropdown(label="Profile", choices=["All"] + h.get_profile_names(auth_state), value="All")
							status_filter = gr.Dropdown(label="Status", choices=["All", "active", "pending", "disabled"], value="All")
					refresh_users_btn = gr.Button("Refresh", variant="secondary")
					table = gr.HTML()
					inputs = [auth_state, search, user_type, status_filter]

					# Update table when filters change
					# for component in inputs:
					# 	component.change(
					# 		h.refresh_users_table,
					# 		inputs=inputs,
					# 		outputs=[table, user_type]
					# 	)
					
					# Update table when refresh button is clicked
					refresh_users_btn.click(
						fn=h.refresh_users_table,
						inputs=inputs,
						outputs=[table, user_type]
					)
				gr.Column(scale=1, min_width=0)

			# New User panel
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=False, scale=0, min_width=800) as new_user_panel:
					new_user_components = h.create_user_form(
						auth_state,
						include_password=True,
						title="New User"
					)
				gr.Column(scale=1, min_width=0)

			# Edit User panel
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=False, scale=0, min_width=800) as edit_user_panel:
					edit_user_components = h.create_user_form(
						auth_state,
						include_user_id=True,
						include_delete=True,
						title="Edit User"
					)
				gr.Column(scale=1, min_width=0)


		uTab.select(h.initial_table_load, inputs=[auth_state], outputs=table)

		# Profiles Tab
		with gr.TabItem("Profiles", id="profile_TabItem") as pTab:
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=True, scale=0, min_width=800) as profiles_panel:
					with gr.Row(elem_classes=["header"]):
						with gr.Column(scale=1):
							gr.Markdown("# Profiles Management")
						with gr.Column(scale=0, min_width=75):
							new_profile_btn = gr.Button("New", variant="stop", elem_classes=["logout-btn"])

					refresh_profiles_btn = gr.Button("Refresh", variant="secondary")
					
					profiles_table = gr.HTML()
					
					# Refresh button functionality
					refresh_profiles_btn.click(
						fn=h.refresh_profiles_table,
						inputs=[auth_state],
						outputs=profiles_table
					)
				gr.Column(scale=1, min_width=0)

			# New Profile panel
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=False, scale=0, min_width=800) as new_profile_panel:
					new_profile_components = h.create_profile_form(
						include_profile_id=False,
						title="New Profile"
					)
				gr.Column(scale=1, min_width=0)

			# Edit Profile panel
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(elem_classes=["container"], visible=False, scale=0, min_width=800) as edit_profile_panel:
					edit_profile_components = h.create_profile_form(
						include_profile_id=True,
						include_delete=True,
						title="Edit Profile"
					)
				gr.Column(scale=1, min_width=0)

		# Load profiles when page loads
		pTab.select(fn=h.refresh_profiles_table, inputs=[auth_state], outputs=profiles_table)            
		


	# Wire login/logout
	login_btn.click(
		h.do_login,
		inputs=[login_user, login_pass, auth_state],
		outputs=[tabs, login_panel, login_message, logout_btn, auth_state, table]
	).then(
		h.refresh_users_table,
		inputs=inputs,
		outputs=[table, user_type]
	)

	logout_btn.click(
		h.do_logout,
		inputs=[auth_state],
		outputs=[tabs, login_panel, login_message, logout_btn, auth_state, login_user, login_pass]
	)
	# .then(
	# 	fn=None,
	# 	inputs=None,
	# 	outputs=None,
	# 	js=f"() => {{ window.location.href = '{APISIX_URL}/logout'; }}"
	# )

	new_user_btn.click(
		h.show_new_user_panel,
		outputs=[users_panel, new_user_panel, edit_user_panel]
	)

	# Wire up user save button
	new_user_components['save_btn'].click(
		h.save_new_user,
		inputs=[auth_state, new_user_components['username'], new_user_components['email'],
				new_user_components['password'], new_user_components['u_type'],
				new_user_components['u_status'], new_user_components['is_federated']],
		outputs=[new_user_components['msg']]
	)

	# Wire up user save button
	edit_user_components['save_btn'].click(
		h.save_user,
		inputs=[auth_state, edit_user_components['user_id'], edit_user_components['username'],
				edit_user_components['email'], edit_user_components['u_type'],
				edit_user_components['u_status'], edit_user_components['is_federated']],
		outputs=[edit_user_components['msg']]
	)

	# Wire up user delete button
	edit_user_components['delete_btn'].click(
		h.delete_user,
		inputs=[auth_state, edit_user_components['user_id']],
		outputs=[edit_user_components['username'], edit_user_components['email'],
				edit_user_components['msg'], edit_user_components['delete_msg']],
		# js="() => { window.location.href = 'http://localhost:7860'; }"
	)

	new_profile_btn.click(
		h.show_new_profile_panel,
		outputs=[
			profiles_panel,
			new_profile_panel,
			edit_profile_panel
		]
	)

	new_profile_components['save_btn'].click(
		h.save_new_profile,
		inputs=[
			auth_state,
			new_profile_components['u_type'],
			new_profile_components['count'],
			new_profile_components['time_window'],
			new_profile_components['rejected_code'],
			new_profile_components['rejected_msg'],
			new_profile_components['policy'],
			new_profile_components['show_limit_quota_header']
		],
		outputs=[new_profile_components['msg']]
	)

	edit_profile_components['save_btn'].click(
		h.save_profile,
		inputs=[
			auth_state,
			edit_profile_components['profile_id'],
			edit_profile_components['u_type'],
			edit_profile_components['count'],
			edit_profile_components['time_window'],
			edit_profile_components['rejected_code'],
			edit_profile_components['rejected_msg'],
			edit_profile_components['policy'],
			edit_profile_components['show_limit_quota_header']
		],
		outputs=[edit_profile_components['msg']]
	)

	edit_profile_components['delete_btn'].click(
		h.delete_profile,
		inputs=[auth_state, edit_profile_components['profile_id']],
		outputs=[
			edit_profile_components['u_type'],
			edit_profile_components['count'],
			edit_profile_components['time_window'],
			edit_profile_components['rejected_code'],
			edit_profile_components['rejected_msg'],
			edit_profile_components['msg'],
			edit_profile_components['delete_msg']
		],
		# js="() => { window.location.href = 'http://localhost:7860'; }"
	)


	@demo.load(
		inputs=[session_state, auth_state], 
		outputs=[
			auth_state, tabs, logout_btn, login_panel,
			users_panel, new_user_panel, edit_user_panel,
			profiles_panel, new_profile_panel, edit_profile_panel,
			edit_user_components['user_id'], edit_profile_components['profile_id']
		]
	)
	def load_web(saved_values, auth_state, request: gr.Request):
		auth = True if saved_values["access_token"] else False
		auth_state["access_token"] = saved_values["access_token"]

		users_panel, new_user_panel, edit_user_panel = h.show_users_panel()
		profiles_panel, new_profile_panel, edit_profile_panel = h.show_profiles_panel()
		user_id, profile_id = h.check_url_params(request)
		tab_item = "user_TabItem"
		if user_id:
			users_panel, new_user_panel, edit_user_panel = h.show_edit_user_panel()
		elif profile_id:
			profiles_panel, new_profile_panel, edit_profile_panel = h.show_edit_profile_panel()
			tab_item = "profile_TabItem"

		return (
			auth_state,			# auth_state
			gr.update(visible=auth, selected=tab_item),	# tabs
			gr.update(visible=auth),						# logout_btn
			gr.update(visible=False if auth else True),	# login_panel
			users_panel,									# users_panel
			new_user_panel,								# new_user_panel
			edit_user_panel,								# edit_user_panel
			profiles_panel,								# profiles_panel
			new_profile_panel,								# new_profile_panel
			edit_profile_panel,								# edit_profile_panel
			user_id,										# user_id
			profile_id										# profile_id
		)

	@gr.on([auth_state.change], inputs=[auth_state], outputs=[session_state])
	def save_to_local_storage(auth_state):
		new_storage={
			"access_token": auth_state["access_token"]
		}
		return new_storage

	@gr.on(
		[edit_user_components['user_id'].change],
		inputs=[edit_user_components['user_id'], auth_state],
		outputs=[
			edit_user_components['form_section'],
			edit_user_components['user_id'],
			edit_user_components['username'],
			edit_user_components['email'],
			edit_user_components['u_type'],
			edit_user_components['u_status'],
			edit_user_components['is_federated'],
			edit_user_components['msg']
		]
	)
	def auto_load_user(user_id, auth_state):
		return h.auto_load_user(user_id, auth_state)

	@gr.on(
		[edit_profile_components['profile_id'].change],
		inputs=[edit_profile_components['profile_id'], auth_state],
		outputs=[
			edit_profile_components['form_section'],
			edit_profile_components['profile_id'],
			edit_profile_components['u_type'],
			edit_profile_components['count'],
			edit_profile_components['time_window'],
			edit_profile_components['rejected_code'],
			edit_profile_components['rejected_msg'],
			edit_profile_components['policy'],
			edit_profile_components['show_limit_quota_header'],
			edit_profile_components['msg']]
	)
	def auto_load_profile(profile_id, auth_state):
		return h.auto_load_profile(profile_id, auth_state)

demo.launch()