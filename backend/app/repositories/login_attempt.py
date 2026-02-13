from datetime import datetime, timedelta
from typing import Optional

from app.repositories.base import BaseRepository
from app.core.exceptions import DatabaseException


class LoginAttemptRepository(BaseRepository[dict]):
    """Repository to track login attempts and locks per (username, ip)."""

    @property
    def table_name(self) -> str:
        # Not used directly (we operate on two tables), but required by BaseRepository
        return "user_db.login_attempts"

    # Attempts
    def record_attempt(self, username: str, ip: str, success: bool) -> None:
        query = (
            f"INSERT INTO {self.table_name} (username, ip, attempted_at, success) "
            f"VALUES (%s, %s, NOW(), %s)"
        )
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, (username, ip, 1 if success else 0))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseException(f"Error recording login attempt: {e}")

    def get_failed_count(self, username: str, ip: str, since: datetime) -> int:
        query = (
            f"SELECT COUNT(*) AS cnt FROM {self.table_name} "
            f"WHERE username=%s AND ip=%s AND success=0 AND attempted_at >= %s"
        )
        try:
            result = self.fetch_one(query, (username, ip, since))
            return int(result.get("cnt", 0)) if result else 0
        except Exception as e:
            raise DatabaseException(f"Error counting failed login attempts: {e}")

    # Locks
    def get_lock_until(self, username: str, ip: str) -> Optional[datetime]:
        query = (
            f"SELECT locked_until FROM user_db.login_locks "
            f"WHERE username=%s AND ip=%s AND locked_until > NOW()"
        )
        try:
            row = self.fetch_one(query, (username, ip))
            return row.get("locked_until") if row else None
        except Exception as e:
            raise DatabaseException(f"Error fetching login lock: {e}")

    def set_lock_until(self, username: str, ip: str, until: datetime) -> None:
        # Upsert by (username, ip)
        query = (
            f"INSERT INTO user_db.login_locks (username, ip, locked_until) "
            f"VALUES (%s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE locked_until=VALUES(locked_until)"
        )
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, (username, ip, until))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseException(f"Error setting login lock: {e}")

    def clear_lock(self, username: str, ip: str) -> None:
        query = f"DELETE FROM user_db.login_locks WHERE username=%s AND ip=%s"
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, (username, ip))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseException(f"Error clearing login lock: {e}")
