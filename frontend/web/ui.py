"""Gradio UI construction and callback wiring.

This module builds the Gradio interface and connects all event handlers.
"""
from __future__ import annotations

import gradio as gr

import handlers as h
import os

# Get base URL from environment variable
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "https://dev.hitz.eus/nlp_tresnak/")
FEDERATION_URL = os.environ.get("FEDERATION_URL", "https://zerbitzuak.hitz.eus/Shibboleth.sso/Login?target=https://zerbitzuak.hitz.eus/zerb_sso")
#FEDERATION_URL = "https://dev.hitz.eus/api/federated_token"
APISIX_URL = os.getenv("APISIX_URL", "https://zerbitzuak.hitz.eus/api")

def build_ui() -> gr.Blocks:
	css = h.load_css_safe("assets/style.css")

	"""Construct and return the Gradio interface with all callbacks connected."""
	with gr.Blocks(title=h.t('header.title'), theme=gr.themes.Soft(), css=css) as demo:
		# State to store authentication
		auth_state = gr.State({"authenticated": False, "token": None, "status": None})
		session_state = gr.BrowserState({"access_token": None, "language": ""})
		# Centralized navigation state
		nav_state = gr.State({"current_modal": None, "previous_modal": None})
		
		# --------------------------------------------------------------------
		# Header Section
		# --------------------------------------------------------------------
		with gr.Row():
			with gr.Column(scale=9):
				header = gr.Markdown(f"{h.t('header.title')}")
			with gr.Column(scale=3, elem_classes=['header-actions']):
				# Actions row: language selector + login buttons
				with gr.Row(variant='compact', elem_classes=['header-actions-row']):
					login_btn = gr.Button(f"{h.t('header.login_button')}", variant="secondary", size="sm")

					federated_login_btn = gr.Button(
						h.t('header.federated_login_button'),
						variant="secondary",
						size="sm",
						link=FEDERATION_URL
					)

					language_selector = gr.Dropdown(
						choices=h.get_available_languages(),
						value=h.get_current_language(),
						label=None,
						interactive=True,
						scale=0,
						container=False,
						min_width=80,
						elem_classes=['minimal-dropdown', 'language-selector']
					)

				with gr.Row():
					user_info = gr.Markdown(f"👤 **{h.t('header.user_label')}**", visible=False)
					profile_btn = gr.Button(h.t('header.profile_button'), variant="secondary", size="sm", visible=False)
				logout_btn = gr.Button(h.t('header.logout_button'), variant="secondary", size="sm", visible=False)


		# --------------------------------------------------------------------
		# Login Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as login_modal:
			is_register_mode = gr.State(False)
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):
					modal_title = gr.Markdown(f"{h.t('authentication.login_modal_title')}")
				
					username_input = gr.Textbox(
						label=h.t('authentication.username_label'),
						placeholder=h.t('authentication.username_placeholder')
					)
					email_input = gr.Textbox(
						label=h.t('authentication.email_label'),
						placeholder=h.t('authentication.email_placeholder'),
						visible=False
					)
					password_input = gr.Textbox(
						label=h.t('authentication.password_label'),
						type="password"
					)
					password_confirm_input = gr.Textbox(
						label=h.t('authentication.password_confirm_label'),
						type="password",
						visible=False
					)

					with gr.Row():
						modal_login_btn = gr.Button(h.t('authentication.login_button'), variant="primary")
						modal_cancel_btn = gr.Button(h.t('authentication.cancel_button'), variant="secondary")

					switch_mode_btn = gr.Button(
						h.t('authentication.switch_to_register'),
						variant="secondary",
						size="sm"
					)

					forgotten_password_btn = gr.Button(
						h.t('authentication.forgot_password'),
						variant="secondary",
						size="sm"
					)
					login_message = gr.Markdown("")

				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# Email Verification Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as email_verification_modal:

			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):
					email_verification_title = gr.Markdown(f"{h.t('email_verification.modal_title')}")
					
					code_input = gr.Textbox(
						label=h.t('email_verification.code_label'),
						placeholder=h.t('email_verification.code_placeholder')
					)
					
					email_verification_message = gr.Markdown("")
					
					resend_verification_btn = gr.Button(
						h.t('email_verification.resend_button'),
						variant="secondary",
						size="sm",
						visible=True
					)
					
					email_verification_btn = gr.Button(h.t('email_verification.verify_button'), variant="primary")
					close_email_verification_btn = gr.Button(h.t('email_verification.close_button'), variant="secondary")

				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# Profile Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as profile_modal:
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):
					profile_title = gr.Markdown(f"{h.t('profile.modal_title')}")
					profile_md = gr.Markdown("")
					resend_verification_btn2 = gr.Button(
						h.t('profile.resend_verification_button'),
						variant="primary",
						size="sm",
						visible=False
					)

					generate_key_btn = gr.Button(h.t('profile.generate_key_button'), variant="primary")
					profile_logout_btn = gr.Button(h.t('profile.logout_button'), variant="secondary")
					close_profile_btn = gr.Button(h.t('profile.close_button'), variant="secondary")
				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# API Key Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as api_key_modal:
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):
					api_key_modal_md = gr.Markdown("")
					api_key_ok_btn = gr.Button(h.t('profile.okay_button'), variant="primary")
				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# Password Reset Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as password_reset_modal:

			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):

					with gr.Row():
						password_reset_title = gr.Markdown(f"{h.t('password_reset.modal_title')}")
					with gr.Row():
						reset_code_input = gr.Textbox(
							label=h.t('password_reset.code_label'),
							placeholder=h.t('password_reset.code_placeholder'),
							visible=True
						)
						reset_email_input = gr.Textbox(
							label=h.t('password_reset.email_label'),
							placeholder=h.t('password_reset.email_placeholder'),
							visible=True
						)
						reset_password_input = gr.Textbox(
							label=h.t('password_reset.password_label'),
							type="password",
							visible=True
						)
						reset_password_confirm_input = gr.Textbox(
							label=h.t('password_reset.password_confirm_label'),
							type="password",
							visible=True
						)
						
					with gr.Row():
						password_reset_message = gr.Markdown("")
					with gr.Row():
						resend_passwd_reset_btn = gr.Button(
							h.t('password_reset.resend_button'),
							variant="secondary",
							size="sm",
							# visible=True
							visible=False
						)
					with gr.Row():
						password_reset_btn = gr.Button(h.t('password_reset.verify_button'), variant="primary")
						close_password_reset_btn = gr.Button(h.t('password_reset.close_button'), variant="secondary")
				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# Password Request (Email-only) Modal
		# --------------------------------------------------------------------
		with gr.Column(visible=False) as password_request_modal:
			with gr.Row():
				gr.Column(scale=1, min_width=0)
				with gr.Column(scale=0, min_width=800):
					with gr.Row():
						password_request_title = gr.Markdown(f"{h.t('password_reset.request_modal_title')}")
					with gr.Row():
						request_email_input = gr.Textbox(
							label=h.t('password_reset.email_label'),
							placeholder=h.t('password_reset.email_placeholder'),
							visible=True
						)
					with gr.Row():
						send_password_request_btn = gr.Button(h.t('password_reset.request_send_button'), variant="primary")
						close_password_request_btn = gr.Button(h.t('password_reset.close_button'), variant="secondary")
					with gr.Row():
						password_request_message = gr.Markdown(h.t('password_reset.note_for_federated'))
				gr.Column(scale=1, min_width=0)

		# --------------------------------------------------------------------
		# Main Content (wrapper) + Tabs
		# --------------------------------------------------------------------
		# Wrap Tabs in a Column so we can toggle visibility via a valid output component
		with gr.Column(visible=True) as main_content:
			with gr.Tabs(visible=True) as tabs:
				# Lemmatizer Tab
				with gr.TabItem(h.t('tabs.lemmatizer')) as lemmatizer_tab:
					with gr.Row():
						gr.Column(scale=1, min_width=0)
						with gr.Column(scale=0, min_width=800):
							lemma_intro_md = gr.Markdown(f"""
								{h.t('lemmatizer.title')}
								{h.t('lemmatizer.description')}
							""")
							# Toggle between text and file input
							lemma_input_type = gr.Radio(
								[h.t('nlp.text_input_option'), h.t('nlp.file_upload_option')],
								label=h.t('nlp.input_type_label'),
								value=h.t('nlp.text_input_option'),
								interactive=False  # Disabled by default, will be enabled on login
							)
						
							# Text input (initially visible)
							lemma_input = gr.Textbox(
								label=h.t('nlp.text_input_label'),
								lines=5,
								placeholder=h.t('nlp.text_input_placeholder'),
								visible=True
							)
							
							# File upload (initially hidden)
							lemma_file = gr.File(
								label=h.t('nlp.file_upload_label'),
								file_types=[".txt", ".pdf"],
								type="filepath",
								visible=False
							)

							# Output format selector
							lemma_output_format = gr.Dropdown(
								choices=[
									h.t('nlp.output_format_web'),
									"txt",
									"json"
									],
									value=h.t('nlp.output_format_web'),
									label=h.t('nlp.output_format_label'),
									interactive=False
							)
						
							lemma_btn = gr.Button(h.t('nlp.analyze_button'), variant="primary")

							lemma_output = gr.HTML(label=h.t('nlp.results_label'), value=h.t('nlp.results_label'), visible=True, min_height=50, max_height=500, container=True)
							lemma_download = gr.File(
								label=h.t('nlp.download_button'), 
								interactive=False, 
								visible=False, 
								elem_classes=["col-auto"]
							)
						gr.Column(scale=1, min_width=0)
			
				# NERC Tab
				with gr.TabItem(h.t('tabs.nerc')) as nerc_tab:
					with gr.Row():
						gr.Column(scale=1, min_width=0)
						with gr.Column(scale=0, min_width=800):
							nerc_intro_md = gr.Markdown(f"""
								{h.t('nerc.title')}
								{h.t('nerc.description')}
							""")
				
							# Toggle between text and file input
							nerc_input_type = gr.Radio(
								[h.t('nlp.text_input_option'), h.t('nlp.file_upload_option')],
								label=h.t('nlp.input_type_label'),
								value=h.t('nlp.text_input_option'),
								interactive=False  # Disabled by default, will be enabled on login
							)
						
							# Text input (initially visible)
							nerc_input = gr.Textbox(
								label=h.t('nlp.text_input_label'),
								lines=5,
								placeholder=h.t('nlp.text_input_placeholder'),
								visible=True
							)
						
							# File upload (initially hidden)
							nerc_file = gr.File(
								label=h.t('nlp.file_upload_label'),
								file_types=[".txt", ".pdf"],
								file_count="single",
								type="filepath",
								visible=False
							)

							# Output format selector
							nerc_output_format = gr.Dropdown(
								choices=[
									h.t('nlp.output_format_web'),
									"txt",
									"json"
								],
								value=h.t('nlp.output_format_web'),
								label=h.t('nlp.output_format_label'),
								interactive=False
							)
						
							nerc_btn = gr.Button(h.t('nlp.analyze_button'), variant="primary")

							nerc_output = gr.HTML(label=h.t('nlp.results_label'), value=h.t('nlp.results_label'), visible=True, min_height=50, max_height=500, container=True)
							nerc_download = gr.File(
								label=h.t('nlp.download_button'), 
								interactive=False,
								visible=False,
								elem_classes=["col-auto"]
							)
						gr.Column(scale=1, min_width=0)
				
					nerc_input_type.change(
						fn=h.toggle_nerc_visibility,
						inputs=nerc_input_type,
						outputs=[nerc_input, nerc_file, nerc_btn]
					)
				
					# Connect Lemma input type toggle
					lemma_input_type.change(
						fn=h.toggle_lemma_visibility,
						inputs=lemma_input_type,
						outputs=[lemma_input, lemma_file, lemma_btn]
					)


		# --------------------------------------------------------------------
		# Event Handlers
		# --------------------------------------------------------------------
		
		# Login/Logout
		login_btn.click(
			lambda ns: h.navigate_to_modal("login", ns),
			inputs=[nav_state],
			outputs=[
				nav_state, login_modal, profile_modal, email_verification_modal,
				password_request_modal, password_reset_modal, api_key_modal, main_content
			]
		)
		
		modal_cancel_btn.click(
			lambda ns: h.navigate_to_modal(None, ns, close_tabs=False),
			inputs=[nav_state],
			outputs=[
				nav_state, login_modal, profile_modal, email_verification_modal,
				password_request_modal, password_reset_modal, api_key_modal, main_content
			]
		)
		
		# Switch between login/register modes
		switch_mode_btn.click(
			h.toggle_register_mode,
			inputs=[is_register_mode],
			outputs=[
				is_register_mode, modal_title, email_input, password_confirm_input,
				modal_login_btn, switch_mode_btn, login_message, username_input,
				password_input, forgotten_password_btn
			]
		)
		
		# Login/Register form submission
		modal_login_btn.click(
			h.handle_modal_login,
			inputs=[
				username_input, email_input, password_input, password_confirm_input,
				auth_state, is_register_mode
			],
			outputs=[
				auth_state, login_message, login_btn, federated_login_btn, profile_btn, user_info,
				logout_btn, login_modal, username_input, password_input,
				main_content, email_verification_modal
			]
		)
		
		# Logout buttons
		for btn in [logout_btn, profile_logout_btn]:
			btn.click(
				h.handle_logout,
				inputs=[auth_state, session_state],
				outputs=[
					auth_state, session_state, login_btn, federated_login_btn, profile_btn, user_info, logout_btn,
					profile_md, profile_modal, main_content
				],
			).then(
				fn=None,
				inputs=None,
				outputs=None,
				js=f"() => {{ window.location.href = '{APISIX_URL}/logout'; }}"
			)

		# Profile
		profile_btn.click(
			lambda ns: h.navigate_to_modal("profile", ns),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)

		profile_btn.click(
			h.get_profile_info,
			inputs=[auth_state],
			outputs=[profile_md, profile_modal, resend_verification_btn2, main_content],
			queue=False
		)
		
		# Create new API key
		generate_key_btn.click(
			h.create_api_key,
			inputs=[auth_state],
			outputs=[api_key_modal_md, api_key_modal, profile_modal]
		)

		# Handle OK button in key modal - close API key modal and return to profile
		api_key_ok_btn.click(
			lambda ns: h.navigate_to_modal("profile", ns),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)
		
		# Update profile info after closing the API key modal
		api_key_ok_btn.click(
			h.get_profile_info,
			inputs=[auth_state],
			outputs=[profile_md, profile_modal, resend_verification_btn2, main_content],
			queue=False  # Run this update without queuing
		)

		close_profile_btn.click(
			lambda ns: h.navigate_to_modal(None, ns, close_tabs=False),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)
		
		# Forgot password -> open password reset modal
		forgotten_password_btn.click(
			lambda ns: h.navigate_to_modal("password_request", ns),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)

		# Close password reset modal
		close_password_reset_btn.click(
			lambda ns: h.navigate_to_modal(None, ns, close_tabs=False),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		).then(
			fn=None,
			inputs=None,
			outputs=None,
			js=f"() => {{ window.location.href = '{WEB_BASE_URL}'; }}"
		)

		# Email-only password request actions
		send_password_request_btn.click(
			h.handle_request_password_reset,
			inputs=[request_email_input],
			outputs=[password_request_message]
		)

		close_password_request_btn.click(
			lambda ns: h.navigate_to_modal(None, ns, close_tabs=False),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)

		# Password reset actions
		# resend_passwd_reset_btn.click(
		#     h.handle_request_password_reset,
		#     inputs=[reset_email_input],
		#     outputs=[password_reset_message]
		# )
		password_reset_btn.click(
			h.handle_password_reset_verify,
			inputs=[reset_code_input, reset_password_input, reset_password_confirm_input],
			outputs=[password_reset_message, password_reset_modal]
		).then(
			fn=None,
			inputs=password_reset_message,
			outputs=None,
			js=f"""
				function(password_reset_message) {{
					if (password_reset_message === 'OK') {{
						window.location.href = '{WEB_BASE_URL}';
					}}
					return [];
			}}
			"""
		)

		# Email verification
		for btn in [resend_verification_btn, resend_verification_btn2]:
			btn.click(
				h.handle_resend_verification,
				inputs=[auth_state],
				outputs=[email_verification_message, email_verification_modal, profile_modal]
			)
		
		email_verification_btn.click(
			h.verify_email,
			inputs=[auth_state, code_input],
			outputs=[email_verification_message, email_verification_modal, main_content]
		)
		
		close_email_verification_btn.click(
			lambda ns: h.navigate_to_modal(None, ns, close_tabs=False),
			inputs=[nav_state],
			outputs=[nav_state, login_modal, profile_modal, email_verification_modal, password_request_modal, password_reset_modal, api_key_modal, main_content]
		)
		
		# NLP Processing
		lemma_btn.click(
			h.lemmatize_text,
			inputs=[
				lemma_input,  # Text input
				lemma_file,   # File upload
				auth_state,   # Authentication state
				lemma_output_format,  # Output format
				lemma_input_type	# Input type (text or file)
			],
			outputs=[lemma_output, lemma_download]
		)
		
		nerc_btn.click(
			h.recognize_entities,
			inputs=[
				nerc_input,   # Text input
				nerc_file,    # File upload
				auth_state,   # Authentication state
				nerc_output_format,  # Output format
				nerc_input_type		# Input type (text or file)
			],
			outputs=[nerc_output, nerc_download]
		)
		
		# Language change -> update key UI strings dynamically
		language_selector.change(
			fn=h.update_interface,
			inputs=[language_selector, is_register_mode, lemma_input_type, nerc_input_type, session_state],
			outputs=[
				# 1 header_md
				header,
				# 2-5 buttons
				login_btn, federated_login_btn, profile_btn, logout_btn,
				# 6-7 tabs labels
				lemmatizer_tab, nerc_tab,
				# 8-9 intros
				lemma_intro_md, nerc_intro_md,
				# 10-14 lemma controls (radio, text, file, btn, output label)
				lemma_input_type, lemma_input, lemma_file, lemma_btn, lemma_output, lemma_output_format,
				# 15-19 nerc controls (radio, text, file, btn, output label)
				nerc_input_type, nerc_input, nerc_file, nerc_btn, nerc_output, nerc_output_format,
				# 20-28 login modal
				modal_title, username_input, email_input, password_input, password_confirm_input,
				modal_login_btn, modal_cancel_btn, switch_mode_btn, forgotten_password_btn,
				# 29-33 email verification modal
				email_verification_title,
				# 30-33 code input + buttons
				code_input, resend_verification_btn, email_verification_btn, close_email_verification_btn,
				# 34-39 profile modal
				profile_title, resend_verification_btn2, generate_key_btn, profile_logout_btn, close_profile_btn, api_key_ok_btn,
				# 40-47 password reset modal
				password_reset_title, reset_code_input, reset_email_input, reset_password_input, reset_password_confirm_input,
				resend_passwd_reset_btn, password_reset_btn, close_password_reset_btn,
				# 48-51 password request modal
				password_request_title, request_email_input, send_password_request_btn, close_password_request_btn,
				# 52 session state
				session_state
			]
		)

		# Update UI when auth state changes
		auth_state.change(
			fn=h.update_from_auth_state,
			inputs=[auth_state, language_selector],
			outputs=[
				session_state,
				login_btn,
				federated_login_btn,
				user_info,
				profile_btn,
				logout_btn,
				nerc_input_type,
				nerc_btn,
				lemma_btn,
				lemma_input_type,
				lemma_output_format,
				nerc_output_format
			]
		)

		# Check existing session
		demo.load(
			fn=h.check_existing_session,
			inputs=[auth_state, session_state],
			outputs=[auth_state, session_state, user_info, language_selector]
		)

		# Initialize from URL: if email and token present, open reset modal with fields prefilled and hidden
		demo.load(
			fn=h.init_from_url,
			inputs=[nav_state],
			outputs=[
				nav_state,
				login_modal, profile_modal, email_verification_modal,
				password_request_modal, password_reset_modal, api_key_modal, main_content,
				reset_email_input, reset_code_input
			]
		)
	return demo
