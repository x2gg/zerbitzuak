import mysql.connector
from mysql.connector import Error
from typing import Generator
from contextlib import contextmanager

from app.core.config import settings
from app.core.exceptions import DatabaseException


def get_db_config():
	"""Get database configuration."""
	return {
		"host": settings.DB_HOST,
		"database": settings.DB_NAME,
		"user": settings.DB_USER,
		"password": settings.DB_PASSWORD,
		"pool_size": settings.DB_POOL_SIZE,
		"pool_reset_session": True,
	}


def get_connection():
	"""Get database connection as a dependency."""
	try:
		conn = mysql.connector.connect(**get_db_config())
		yield conn
	except Error as e:
		raise DatabaseException(str(e))
	finally:
		if 'conn' in locals() and conn.is_connected():
			conn.close()


@contextmanager
def get_db():
	"""Get database connection as a context manager."""
	conn = None
	try:
		conn = mysql.connector.connect(**get_db_config())
		yield conn
	except Error as e:
		if conn:
			conn.rollback()
		raise DatabaseException(str(e))
	finally:
		if conn and conn.is_connected():
			conn.close()


def check_db_connection() -> bool:
	"""Check if database connection is working."""
	try:
		conn = mysql.connector.connect(**get_db_config())
		cursor = conn.cursor()
		cursor.execute("SELECT 1")
		cursor.fetchone()
		cursor.close()
		conn.close()
		return True
	except Exception:
		return False