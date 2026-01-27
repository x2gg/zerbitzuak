import smtplib
import random
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)


class EmailService:
	"""Service for sending emails with verification codes."""
	
	def __init__(self):
		self.smtp_host = settings.SMTP_HOST
		self.smtp_port = settings.SMTP_PORT
		self.smtp_username = settings.SMTP_USERNAME
		self.smtp_password = settings.SMTP_PASSWORD
		self.from_email = settings.SMTP_FROM_EMAIL
		self.from_name = settings.SMTP_FROM_NAME
	
	def generate_verification_code(self) -> str:
		"""Generate a 6-digit verification code."""
		return ''.join(random.choices(string.digits, k=6))
	
	async def send_verification_email(
		self, 
		to_email: str, 
		username: str, 
		verification_code: str,
		retry_count: int = 0
	) -> Dict[str, Any]:
		"""
		Send verification email.
		Returns dict with status and message.
		"""
		# Check if SMTP is configured
		if not self.smtp_username or not self.smtp_password:
			logger.warning("SMTP credentials not configured")
			return {
				"success": False,
				"message": "Email service error",
				"error": "SMTP credentials missing"
			}
		
		# Skip sending email to test emails
		if to_email.endswith("@example.com"):
			logger.info(f"Skipping email send to {to_email}")
			return {
				"success": True,
				"message": "Test email sent successfully",
				"email": to_email
			}
		
		subject = f"Verify your account"
		
		# HTML template
		html_body = f"""
		<html>
			<body style="font-family: Arial, sans-serif; padding: 20px;">
				<div style="max-width: 600px; margin: 0 auto;">
					<h2 style="color: #333;">Hi {username}!</h2>
					<p style="color: #555;">Thanks for signing up. Your verification code is:</p>
					<div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
						<h1 style="color: #4CAF50; font-size: 36px; letter-spacing: 5px; margin: 0;">{verification_code}</h1>
					</div>
					<p style="color: #555;">This code will expire in {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes.</p>
					<hr style="border: 1px solid #eee; margin: 20px 0;">
					<p style="color: #999; font-size: 12px;">If you didn't request this code, you can ignore this email.</p>
				</div>
			</body>
		</html>
		"""
		
		# Plain text fallback
		text_body = f"""
Hi {username}!

Thanks for signing up. Your verification code is: {verification_code}

This code will expire in {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes.

If you didn't request this code, you can ignore this email.

Best regards,
{settings.PROJECT_NAME}
		"""
		
		try:
			msg = MIMEMultipart('alternative')
			msg['Subject'] = subject
			msg['From'] = f"{self.from_name} <{self.from_email}>"
			msg['To'] = to_email
			
			msg.attach(MIMEText(text_body, 'plain'))
			msg.attach(MIMEText(html_body, 'html'))
			
			# Send with timeout
			with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
				if settings.SMTP_TLS:
					server.starttls()
				server.login(self.smtp_username, self.smtp_password)
				server.send_message(msg)
			
			logger.info(f"Verification email sent successfully to {to_email}")
			return {
				"success": True,
				"message": "Email sent successfully",
				"email": to_email
			}
			
		except smtplib.SMTPAuthenticationError:
			logger.error(f"SMTP authentication failed for {to_email}")
			return {
				"success": False,
				"message": "Email authentication failed",
				"error": "Invalid SMTP credentials"
			}
		except smtplib.SMTPException as e:
			logger.error(f"SMTP error sending to {to_email}: {str(e)}")
			
			# Retry logic
			if retry_count < settings.MAX_EMAIL_RETRY_ATTEMPTS:
				logger.info(f"Retrying email send (attempt {retry_count + 1})")
				return await self.send_verification_email(
					to_email, username, verification_code, retry_count + 1
				)
			
			return {
				"success": False,
				"message": "Failed to send email",
				"error": str(e)
			}
		except Exception as e:
			logger.error(f"Unexpected error sending to {to_email}: {str(e)}")
			return {
				"success": False,
				"message": "An unexpected error occurred",
				"error": str(e)
			}

	async def send_password_recovery_email(
		self,
		to_email: str,
		username: str,
		recovery_link: str,
		retry_count: int = 0
	) -> Dict[str, Any]:
		"""Send password recovery email with a reset link."""
		if not self.smtp_username or not self.smtp_password:
			logger.warning("SMTP credentials not configured")
			return {
				"success": False,
				"message": "Email service error",
				"error": "SMTP credentials missing"
			}

		if to_email.endswith("@example.com"):
			logger.info(f"Skipping email send to {to_email}")
			return {
				"success": True,
				"message": "Test email sent successfully",
				"email": to_email
			}

		subject = "Password Reset Instructions"
		html_body = f"""
		<html>
			<body style="font-family: Arial, sans-serif; padding: 20px;">
				<div style="max-width: 600px; margin: 0 auto;">
					<h2 style="color: #333;">Hi {username},</h2>
					<p style="color: #555;">We received a request to reset your password. Click the button below to reset it:</p>
					<p style="text-align:center; margin: 24px 0;">
						<a href="{recovery_link}" style="background: #4CAF50; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px;">Reset Password</a>
					</p>
					<p style="color: #555;">If the button doesn't work, copy and paste this link into your browser:</p>
					<p style="word-break: break-all; color: #777;">{recovery_link}</p>
					<p style="color: #999; font-size: 12px;">If you didn't request this, you can ignore this email.</p>
				</div>
			</body>
		</html>
		"""
		text_body = f"""
Hi {username},

We received a request to reset your password. Open this link to reset it:
{recovery_link}

If you didn't request this, you can ignore this email.

Best regards,
{settings.PROJECT_NAME}
		"""

		try:
			msg = MIMEMultipart('alternative')
			msg['Subject'] = subject
			msg['From'] = f"{self.from_name} <{self.from_email}>"
			msg['To'] = to_email

			msg.attach(MIMEText(text_body, 'plain'))
			msg.attach(MIMEText(html_body, 'html'))

			with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
				if settings.SMTP_TLS:
					server.starttls()
				server.login(self.smtp_username, self.smtp_password)
				server.send_message(msg)

			logger.info(f"Password recovery email sent successfully to {to_email}")
			return {
				"success": True,
				"message": "Email sent successfully",
				"email": to_email
			}
		except smtplib.SMTPAuthenticationError:
			logger.error(f"SMTP authentication failed for {to_email}")
			return {
				"success": False,
				"message": "Email authentication failed",
				"error": "Invalid SMTP credentials"
			}
		except smtplib.SMTPException as e:
			logger.error(f"SMTP error sending to {to_email}: {str(e)}")
			if retry_count < settings.MAX_EMAIL_RETRY_ATTEMPTS:
				logger.info(f"Retrying email send (attempt {retry_count + 1})")
				return await self.send_password_recovery_email(
					to_email, username, recovery_link, retry_count + 1
				)
			return {
				"success": False,
				"message": "Failed to send email",
				"error": str(e)
			}
		except Exception as e:
			logger.error(f"Unexpected error sending to {to_email}: {str(e)}")
			return {
				"success": False,
				"message": "An unexpected error occurred",
				"error": str(e)
			}