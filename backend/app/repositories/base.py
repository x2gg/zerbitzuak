from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from mysql.connector import Error

from app.db.utils import dict_from_row, rows_to_dict_list
from app.core.exceptions import DatabaseException
from contextlib import contextmanager


T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
	"""Base repository with common CRUD operations."""
	
	def __init__(self, connection):
		self.connection = connection
		self.cursor = connection.cursor()

	@contextmanager
	def _get_cursor(self):
		cursor = None
		try:
			cursor = self.connection.cursor(dictionary=True)
			yield cursor
		except Error as e:
			if cursor:
				cursor.close()
			raise DatabaseException(str(e))
		finally:
			if cursor:
				cursor.close()
		
	@property
	@abstractmethod
	def table_name(self) -> str:
		"""Return the table name for this repository."""
		pass
	
	def execute_query(self, query: str, params: tuple = None) -> None:
		"""Execute a query without returning results."""
		try:
			if params:
				self.cursor.execute(query, params)
			else:
				self.cursor.execute(query)
		except Error as e:
			raise DatabaseException(str(e))
	
	def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
		"""Execute a query and return one result."""
		try:
			if params:
				self.cursor.execute(query, params)
			else:
				self.cursor.execute(query)
			result = self.cursor.fetchone()
			return dict_from_row(self.cursor, result) if result else None
		except Error as e:
			raise DatabaseException(str(e))
	
	def fetch_many(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
		"""Execute a query and return multiple results."""
		try:
			if params:
				self.cursor.execute(query, params)
			else:
				self.cursor.execute(query)
			results = self.cursor.fetchall()
			return rows_to_dict_list(self.cursor, results)
		except Error as e:
			raise DatabaseException(str(e))
	
	def commit(self) -> None:
		"""Commit the current transaction."""
		try:
			self.connection.commit()
		except Error as e:
			self.rollback()
			raise DatabaseException(str(e))
	
	def rollback(self) -> None:
		"""Rollback the current transaction."""
		try:
			self.connection.rollback()
		except Error as e:
			raise DatabaseException(str(e))
	
	def close(self) -> None:
		"""Close cursor."""
		if self.cursor:
			self.cursor.close()