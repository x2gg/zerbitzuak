from datetime import datetime, timedelta
from typing import Optional

from app.repositories.login_attempt import LoginAttemptRepository
from app.core.config import settings


class LoginThrottleService:
    """Service implementing login attempt limiting per (username, ip)."""

    def __init__(self, repo: LoginAttemptRepository):
        self.repo = repo

    def is_locked(self, username: str, ip: str) -> Optional[datetime]:
        return self.repo.get_lock_until(username, ip)

    def register_failure_and_lock_if_needed(self, username: str, ip: str) -> Optional[datetime]:
        now = datetime.now()
        window_since = now - timedelta(minutes=settings.LOGIN_WINDOW_MINUTES)

        # Count current failures in window
        failures = self.repo.get_failed_count(username, ip, window_since)

        # Record this failure
        self.repo.record_attempt(username, ip, success=False)

        # If this failure reaches the threshold, set lock
        if failures + 1 >= settings.LOGIN_MAX_ATTEMPTS:
            locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            self.repo.set_lock_until(username, ip, locked_until)
            return locked_until
        return None

    def on_success(self, username: str, ip: str) -> None:
        # Record success and clear any existing lock
        self.repo.record_attempt(username, ip, success=True)
        self.repo.clear_lock(username, ip)
